from typing import Iterable

from django.db.models import Max, Min

from reservations.models import Reservable, Reservation


def annotate_overlaps(reservations: Iterable[Reservation]) -> list[Reservation]:
    """Annotate each reservation with the other reservations it overlaps with.

    Fetches every reservation sharing a reservable with one of `reservations` within
    the overall time range of `reservations`, then checks pairwise overlap in Python.
    Sets `.overlaps_with` (a list of `Reservation`) on every reservation in the input.
    """
    reservations = list(reservations)
    if not reservations:
        return []

    bounds = Reservation.objects.filter(
        pk__in=[r.pk for r in reservations]
    ).aggregate(min_start=Min("start"), max_end=Max("end"))
    min_start, max_end = bounds["min_start"], bounds["max_end"]

    reservables = Reservable.objects.filter(reservations__in=reservations).distinct()

    candidates = list(
        Reservation.objects.filter(
            start__lt=max_end, end__gt=min_start, reservables__in=reservables
        )
        .distinct()
        .prefetch_related("reservables")
    )

    # Reuse the already-fetched candidate for any reservation that's also a candidate,
    # so its reservables come from the prefetch cache instead of a fresh query.
    by_pk = {c.pk: c for c in candidates}
    for r in reservations:
        by_pk.setdefault(r.pk, r)
    candidates = list(by_pk.values())

    reservable_ids = {c.pk: {rb.pk for rb in c.reservables.all()} for c in candidates}

    for reservation in reservations:
        my_reservables = reservable_ids.get(reservation.pk, set())
        overlaps = []
        if my_reservables:
            for other in candidates:
                if other.pk == reservation.pk:
                    continue
                if not (reservation.start < other.end and reservation.end > other.start):
                    continue
                if reservable_ids.get(other.pk, set()) & my_reservables:
                    overlaps.append(other)
        reservation.overlaps_with = overlaps

    return reservations
