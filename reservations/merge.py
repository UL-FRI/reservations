from itertools import chain
from typing import Iterable

from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel

from reservations.models import Reservable, Reservation


def merge_reservables(primary: Reservable, others: Iterable[Reservable]):
    total_before = (
        (Reservation.objects.filter(reservables=primary) | Reservation.objects.filter(reservables__in=others))
        .distinct()
        .count()
    )

    for reservable in others:
        # Update all reservations that include the reservable to be merged
        for reservation in reservable.reservations.all():
            reservation.reservables.remove(reservable)
            reservation.reservables.add(primary)
            reservation.save()
            print(f"Updated reservation {reservation.id} to replace reservable {reservable.id} with {primary.id}")

        # Update all foreign reservables
        for fr in reservable.foreignreservable_set.all():
            fr.reservable = primary
            fr.save()
            print(f"Updated ForeignReservable {fr.id} to point to reservable {primary.id} instead of {reservable.id}")

        # Delete the original
        Reservable.objects.filter(id=reservable.id).delete()

    total_after = Reservation.objects.filter(reservables=primary).distinct().count()

    if total_before != total_after:
        raise Exception(
            f"Expected {total_before} reservations to be updated, but found {total_after} after merging. Please check the data integrity."
        )
