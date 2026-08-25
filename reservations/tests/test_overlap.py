from django.test import TestCase
from datetime import datetime
from django.utils import timezone

from reservations.models import Reservable, Reservation


class OverlapTests(TestCase):
    def setUp(self):
        self.reservable = Reservable.objects.create(slug='room1', type='room', name='Room 1')

    def test_adjacent_intervals_not_overlapping(self):
        start1 = timezone.make_aware(datetime(2023, 1, 1, 13, 0))
        end1 = timezone.make_aware(datetime(2023, 1, 1, 14, 0))
        start2 = timezone.make_aware(datetime(2023, 1, 1, 14, 0))
        end2 = timezone.make_aware(datetime(2023, 1, 1, 15, 0))
        r1 = Reservation.objects.create(start=start1, end=end1)
        r1.reservables.add(self.reservable)
        qs = Reservation.objects.overlapping(start2, end2, Reservable.objects.filter(pk=self.reservable.pk))
        self.assertFalse(qs.filter(pk=r1.pk).exists())

    def test_partial_overlap(self):
        # Existing reservation 13:00-15:00, new reservation 14:00-16:00 should overlap
        start1 = timezone.make_aware(datetime(2023, 1, 1, 13, 0))
        end1 = timezone.make_aware(datetime(2023, 1, 1, 15, 0))
        start2 = timezone.make_aware(datetime(2023, 1, 1, 14, 0))
        end2 = timezone.make_aware(datetime(2023, 1, 1, 16, 0))
        r1 = Reservation.objects.create(start=start1, end=end1)
        r1.reservables.add(self.reservable)
        qs = Reservation.objects.overlapping(start2, end2, Reservable.objects.filter(pk=self.reservable.pk))
        self.assertTrue(qs.filter(pk=r1.pk).exists())

    def test_inner_overlap(self):
        # Existing reservation 13:00-16:00, new reservation 14:00-15:00 should overlap (inner)
        start1 = timezone.make_aware(datetime(2023, 1, 1, 13, 0))
        end1 = timezone.make_aware(datetime(2023, 1, 1, 16, 0))
        start2 = timezone.make_aware(datetime(2023, 1, 1, 14, 0))
        end2 = timezone.make_aware(datetime(2023, 1, 1, 15, 0))
        r1 = Reservation.objects.create(start=start1, end=end1)
        r1.reservables.add(self.reservable)
        qs = Reservation.objects.overlapping(start2, end2, Reservable.objects.filter(pk=self.reservable.pk))
        self.assertTrue(qs.filter(pk=r1.pk).exists())

    def test_perfect_overlap(self):
        # Existing reservation 13:00-15:00, new reservation exactly the same should overlap
        start1 = timezone.make_aware(datetime(2023, 1, 1, 13, 0))
        end1 = timezone.make_aware(datetime(2023, 1, 1, 15, 0))
        start2 = timezone.make_aware(datetime(2023, 1, 1, 13, 0))
        end2 = timezone.make_aware(datetime(2023, 1, 1, 15, 0))
        r1 = Reservation.objects.create(start=start1, end=end1)
        r1.reservables.add(self.reservable)
        qs = Reservation.objects.overlapping(start2, end2, Reservable.objects.filter(pk=self.reservable.pk))
        self.assertTrue(qs.filter(pk=r1.pk).exists())
    def setUp(self):
        self.reservable = Reservable.objects.create(slug='room1', type='room', name='Room 1')
