from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.test import Client, TestCase
from django.urls import reverse
from reservations.models import Reservable, ReservableSet, Reservation


User: Type[AbstractUser] = get_user_model()


class ReservationTestDataMixin:
    """Mixin that provides common test data setup for both API and form-based tests."""

    @classmethod
    def setUpTestData(cls):
        cls.group_fri_prof = Group.objects.create(name="fri_prof")
        cls.profesor = User.objects.create(
            first_name="Profesor",
            last_name="Pametni",
            email="prof@fri.uni-lj.si",
            username="prof@fri.uni-lj.si",
        )
        cls.profesor.groups.add(cls.group_fri_prof)

        cls.fri = ReservableSet.objects.create(name="Fri rezervacije", slug="rezervacije_fri")
        cls.p22 = Reservable.objects.create(name="P22", slug="P22", type="classroom")
        cls.p22.reservableset_set.add(cls.fri)

        for codename in ("view_reservation", "add_reservation", "change_reservation", "delete_reservation"):
            cls.group_fri_prof.permissions.add(
                Permission.objects.get(codename=codename, content_type__app_label="reservations")
            )

        cls.r1 = Reservation.objects.create(
            start="2024-06-03T10:00:00Z", end="2024-06-03T11:00:00Z", reason="Reservation 1"
        )
        cls.r1.reservables.add(cls.p22)
        cls.r1.owners.add(cls.profesor)


class HTMLFormPermissionTests(ReservationTestDataMixin, TestCase):
    """Test permissions and rendering for HTML form-based views."""

    def setUp(self):
        self.client = Client()

    def test_reservation_detail_shows_owner_name(self):
        """The reservation detail page should show the owner's name, not 'auth.User.None'."""
        self.client.force_login(self.profesor)
        response = self.client.get(reverse("reservation_detail", kwargs={"pk": self.r1.pk}))
        self.assertContains(response, self.profesor.username)
        self.assertNotContains(response, "auth.User.None")
