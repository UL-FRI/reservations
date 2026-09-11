"""Signal handlers for the reservations application."""

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from reservations.models import Reservation
from reservations.permissions import sync_reservation_owner_permissions


@receiver(m2m_changed, sender=Reservation.owners.through)
def owners_changed(sender, instance, action, reverse, pk_set, **kwargs):
    """Keep guardian object permissions in sync whenever a reservation's owners change.

    Fires regardless of how ``owners`` was modified - form save, admin, API, or the Django shell - since all of those go through the M2M manager.
    """
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    if reverse:
        # instance is a User; pk_set are the affected Reservation pks (None on clear).
        reservations = Reservation.objects.filter(pk__in=pk_set) if pk_set else []
    else:
        # instance is the Reservation whose owners changed.
        reservations = [instance]

    for reservation in reservations:
        sync_reservation_owner_permissions(reservation)
