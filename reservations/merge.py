import logging
from typing import Iterable

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.shortcuts import assign_perm

from reservations.models import Reservable, Reservation

logger = logging.getLogger(__name__)

def merge_reservables(primary: Reservable, others: Iterable[Reservable], dry_run: bool = False):
    """Merge `others` into `primary`.

    Every reservation, reservable set membership, countable resource,
    foreign reservable link (e.g. UrnikTeacher/UrnikClassroom) and guardian
    object permission held by one of `others` is moved onto `primary`, then
    `others` are deleted.

    Pass dry_run=True to only print what would happen: the merge still runs,
    but inside a transaction that is rolled back at the end.
    """
    others = [o for o in others if o.pk != primary.pk]
    content_type = ContentType.objects.get_for_model(Reservable)

    with transaction.atomic():
        total_before = (
            Reservation.objects.filter(reservables=primary)
            | Reservation.objects.filter(reservables__in=others)
        ).distinct().count()

        for reservable in others:
            # Update all reservations that include the reservable to be merged
            for reservation in reservable.reservations.all():
                logger.debug(f"Updated reservation {reservation.id} to replace reservable {reservable.id} with {primary.id}")
                reservation.reservables.remove(reservable)
                reservation.reservables.add(primary)

            # Keep membership in any ReservableSet the duplicate was part of
            for rs in reservable.reservableset_set.all():
                logger.debug(f"Updated ReservableSet '{rs.slug}' to replace reservable {reservable.id} with {primary.id}")
                rs.reservables.add(primary)
                rs.reservables.remove(reservable)

            # Update all foreign reservables
            for fr in reservable.foreignreservable_set.all():
                fr.reservable = primary
                fr.save()
                logger.debug(f"Updated ForeignReservable {fr.id} to point to reservable {primary.id} instead of {reservable.id}")

            # Carry over guardian object permissions (user and group), instead of losing them
            for perm in UserObjectPermission.objects.filter(content_type=content_type, object_pk=str(reservable.pk)):
                logger.debug(f"Granted guardian perm '{perm.permission.codename}' to user {perm.user} on reservable {primary.id}")
                assign_perm(perm.permission.codename, perm.user, primary)
            for perm in GroupObjectPermission.objects.filter(content_type=content_type, object_pk=str(reservable.pk)):
                logger.debug(f"Granted guardian perm '{perm.permission.codename}' to group {perm.group} on reservable {primary.id}")
                assign_perm(perm.permission.codename, perm.group, primary)
            UserObjectPermission.objects.filter(content_type=content_type, object_pk=str(reservable.pk)).delete()
            GroupObjectPermission.objects.filter(content_type=content_type, object_pk=str(reservable.pk)).delete()

            # Delete the original
            logger.info(f"Deleted reservable {reservable.id} ({reservable.name})")
            reservable.delete()

        total_after = Reservation.objects.filter(reservables=primary).distinct().count()

        if total_before != total_after:
            raise Exception(
                f"Expected {total_before} reservations to be updated, but found {total_after} after merging. Please check the data integrity."
            )

        if dry_run:
            logger.info("Dry run - rolling back, nothing was actually changed.")
            transaction.set_rollback(True)
