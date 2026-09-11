from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from reservations.overlaps import annotate_overlaps
from reservations.models import Reservable, ReservableType, Reservation


class AnnotateOverlapsTests(TestCase):
    def setUp(self):
        room_type = ReservableType.objects.create(slug="room", display_name="Room")
        self.room1 = Reservable.objects.create(slug="room1", type=room_type, name="Room 1")
        self.room2 = Reservable.objects.create(slug="room2", type=room_type, name="Room 2")

    def make(self, room, start, end):
        r = Reservation.objects.create(
            start=timezone.make_aware(start), end=timezone.make_aware(end)
        )
        r.reservables.add(room)
        return r

    def test_empty_input(self):
        self.assertEqual(annotate_overlaps(Reservation.objects.none()), [])

    def test_no_overlap(self):
        r1 = self.make(self.room1, datetime(2023, 1, 1, 13, 0), datetime(2023, 1, 1, 14, 0))
        r2 = self.make(self.room1, datetime(2023, 1, 1, 14, 0), datetime(2023, 1, 1, 15, 0))
        result = annotate_overlaps(Reservation.objects.filter(pk__in=[r1.pk, r2.pk]))
        overlaps = {r.pk: r.overlaps_with for r in result}
        self.assertEqual(overlaps[r1.pk], [])
        self.assertEqual(overlaps[r2.pk], [])

    def test_overlap_same_reservable(self):
        r1 = self.make(self.room1, datetime(2023, 1, 1, 13, 0), datetime(2023, 1, 1, 15, 0))
        r2 = self.make(self.room1, datetime(2023, 1, 1, 14, 0), datetime(2023, 1, 1, 16, 0))
        result = annotate_overlaps(Reservation.objects.filter(pk__in=[r1.pk, r2.pk]))
        overlaps = {r.pk: [o.pk for o in r.overlaps_with] for r in result}
        self.assertEqual(overlaps[r1.pk], [r2.pk])
        self.assertEqual(overlaps[r2.pk], [r1.pk])

    def test_overlap_different_reservable_not_flagged(self):
        r1 = self.make(self.room1, datetime(2023, 1, 1, 13, 0), datetime(2023, 1, 1, 15, 0))
        r2 = self.make(self.room2, datetime(2023, 1, 1, 14, 0), datetime(2023, 1, 1, 16, 0))
        result = annotate_overlaps(Reservation.objects.filter(pk__in=[r1.pk, r2.pk]))
        overlaps = {r.pk: r.overlaps_with for r in result}
        self.assertEqual(overlaps[r1.pk], [])
        self.assertEqual(overlaps[r2.pk], [])

    def test_overlap_from_outside_displayed_set(self):
        # r2 is not in the displayed queryset but should still be detected as an overlap for r1.
        r1 = self.make(self.room1, datetime(2023, 1, 1, 13, 0), datetime(2023, 1, 1, 15, 0))
        r2 = self.make(self.room1, datetime(2023, 1, 1, 14, 0), datetime(2023, 1, 1, 16, 0))
        result = annotate_overlaps(Reservation.objects.filter(pk=r1.pk))
        self.assertEqual([o.pk for o in result[0].overlaps_with], [r2.pk])
