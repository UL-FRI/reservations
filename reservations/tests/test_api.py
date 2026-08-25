from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.test import Client, TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm
from reservations.models import Reservable, ReservableSet, Reservation
from rest_framework import status
from rest_framework.test import APITestCase


User: Type[AbstractUser] = get_user_model()

test_week = "2024-06-03T00:00:00Z", "2024-06-09T23:59:59Z"


class ReservationTestDataMixin:
    """Mixin that provides common test data setup for both API and form-based tests."""

    @classmethod
    def setUpTestData(cls):
        # Create users and groups. Both professors can reserve; only prof2 can double-reserve.
        cls.group_fri_prof = Group.objects.create(name="fri_prof")
        cls.profesor = User.objects.create(
            first_name="Profesor",
            last_name="Pametni",
            email="prof@fri.uni-lj.si",
            username="prof@fri.uni-lj.si",
        )
        cls.profesor2 = User.objects.create(
            first_name="Profesor",
            last_name="Pametnejši",
            email="prof2@fri.uni-lj.si",
            username="prof2@fri.uni-lj.si",
        )
        cls.profesor.groups.add(cls.group_fri_prof)
        cls.profesor2.groups.add(cls.group_fri_prof)
        cls.student = User.objects.create(
            first_name="Študent",
            last_name="Glupi",
            email="sg1234@student.uni-lj.si",
            username="sg1234@student.uni-lj.si",
        )
        # Create reservablesets and some classrooms
        cls.fri = ReservableSet.objects.create(name="Fri rezervacije", slug="rezervacije_fri")
        cls.fkkt = ReservableSet.objects.create(name="FKKT rezervacije", slug="rezervacije_fkkt")
        cls.p22 = Reservable.objects.create(name="P22", slug="P22", type="classroom")
        cls.p22.reservableset_set.add(cls.fri)
        cls.pb = Reservable.objects.create(name="PB", slug="PB", type="classroom")
        cls.pb.reservableset_set.add(cls.fkkt)
        cls.pa = Reservable.objects.create(name="PA", slug="PA", type="classroom")
        cls.pa.reservableset_set.add(cls.fri, cls.fkkt)

        # Set up permissions (both profs can reserve, only prof2 can double-reserve)
        for codename in (
            "view_reservable",
            "view_reservation",
            "add_reservation",
            "change_reservation",
            "delete_reservation",
        ):
            cls.group_fri_prof.permissions.add(
                Permission.objects.get(codename=codename, content_type__app_label="reservations")
            )

        assign_perm("reserve", cls.group_fri_prof, cls.fri.reservables.all())
        assign_perm("double_reserve", cls.profesor2, cls.fri.reservables.all())

        # Create some sample reservations, with ownership/edit rights set up the way
        # ReservationCreateView would set them up for a real user-created reservation.
        cls.r1 = Reservation.objects.create(
            start="2024-06-03T10:00:00Z", end="2024-06-03T11:00:00Z", reason="Reservation 1"
        )
        cls.r1.reservables.add(cls.p22)
        cls.r1.owners.add(cls.profesor)
        assign_perm("reservations.change_reservation", cls.profesor, cls.r1)
        assign_perm("reservations.delete_reservation", cls.profesor, cls.r1)

        cls.r2 = Reservation.objects.create(
            start="2024-06-04T10:00:00Z", end="2024-06-04T11:00:00Z", reason="Reservation 2"
        )
        cls.r2.reservables.add(cls.pa)
        cls.r2.owners.add(cls.profesor2)
        assign_perm("reservations.change_reservation", cls.profesor2, cls.r2)
        assign_perm("reservations.delete_reservation", cls.profesor2, cls.r2)


class PermissionTests(ReservationTestDataMixin, APITestCase):
    """Test API permissions for reservations."""

    #
    # RESERVABLES
    #
    def test_student_read_reservables(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/reservables/?reservableset_set__slug={self.fri.slug}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(len(response.data["results"]), 2)

    #
    # RESERVATIONS
    #

    def test_student_read_reservations(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(
            f"/api/reservations/?reservables__reservableset_set__slug={self.fri.slug}&start__gte={test_week[0]}&end__lte={test_week[1]}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(len(response.data["results"]), 2)

    def test_profesor_create_reservation(self):
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(
            "/api/reservations/",
            {
                "start": "2024-06-02T10:00:00Z",
                "end": "2024-06-02T11:00:00Z",
                "reason": "Testing",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

    #
    # CREATED / UPDATED TIMESTAMPS
    #

    def test_reservation_created_and_updated_timestamps(self):
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(
            "/api/reservations/",
            {
                "start": "2024-06-02T10:00:00Z",
                "end": "2024-06-02T11:00:00Z",
                "reason": "Timestamp test",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

        reservation = Reservation.objects.get(pk=response.data["id"])
        # Ownership isn't settable through the (read-only) API "owners" field; add it
        # directly so the subsequent update is permitted.
        reservation.owners.add(self.profesor)
        created_at = reservation.created_at
        updated_at = reservation.updated_at

        response = self.client.patch(
            f"/api/reservations/{reservation.id}/",
            {
                "reason": "Timestamp test, updated",
                "start": "2024-06-02T10:00:00Z",
                "end": "2024-06-02T11:00:00Z",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        reservation.refresh_from_db()
        self.assertEqual(reservation.created_at, created_at)
        self.assertGreater(reservation.updated_at, updated_at)

    #
    # EDITING A MULTI-RESERVABLE RESERVATION (regression test)
    #

    def test_edit_reservation_remove_one_reservable_no_crash(self):
        """Removing one reservable from a multi-reservable reservation must not 500.

        Regression test: the reservation used to be seen as "overlapping itself"
        during the permission check, which crashed instead of just excluding it.
        """
        reservation = Reservation.objects.create(
            start="2024-06-05T10:00:00Z", end="2024-06-05T11:00:00Z", reason="Multi-room booking"
        )
        reservation.reservables.add(self.p22, self.pa)
        reservation.owners.add(self.profesor)

        self.client.force_authenticate(user=self.profesor)
        response = self.client.patch(
            f"/api/reservations/{reservation.id}/",
            {
                "reason": "Multi-room booking",
                "start": "2024-06-05T10:00:00Z",
                "end": "2024-06-05T11:00:00Z",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(list(reservation.reservables.values_list("id", flat=True)), [self.p22.id])

    #
    # DOUBLE-RESERVING
    #

    def test_profesor_double_reserve(self):
        self.client.force_authenticate(user=self.profesor)
        response = self.client.post(
            "/api/reservations/",
            {
                "start": "2024-06-03T10:30:00Z",
                "end": "2024-06-03T11:30:00Z",
                "reason": "Testing double booking",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())
        self.assertContains(response, "No double booking", status_code=status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.profesor2)
        response = self.client.post(
            "/api/reservations/",
            {
                "start": "2024-06-03T10:30:00Z",
                "end": "2024-06-03T11:30:00Z",
                "reason": "Testing double booking",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

    def test_profesor_update_to_overlap_denied(self):
        """Professor without double_reserve should not be able to move a reservation onto another's slot."""
        self.client.force_authenticate(user=self.profesor)
        response = self.client.patch(
            f"/api/reservations/{self.r1.id}/",
            {
                "reason": "Moved into r2's slot",
                "start": "2024-06-04T10:30:00Z",
                "end": "2024-06-04T11:30:00Z",
                "reservables": [self.pa.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.json())
        self.r1.refresh_from_db()
        self.assertEqual(self.r1.reason, "Reservation 1")

    def test_profesor2_update_to_overlap_allowed(self):
        """Professor with double_reserve should be able to move a reservation onto another's slot."""
        self.client.force_authenticate(user=self.profesor2)
        response = self.client.patch(
            f"/api/reservations/{self.r2.id}/",
            {
                "reason": "Moved into r1's slot",
                "start": "2024-06-03T10:30:00Z",
                "end": "2024-06-03T11:30:00Z",
                "reservables": [self.p22.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.r2.refresh_from_db()
        self.assertEqual(self.r2.reason, "Moved into r1's slot")


class HTMLFormPermissionTests(ReservationTestDataMixin, TestCase):
    """Test permissions for HTML form-based views (ReservationCreateView and ReservationUpdateView)."""

    def setUp(self):
        self.client = Client()

    #
    # RESERVATION CREATE VIEW
    #

    def test_professor_create_reservation_get(self):
        """Professor with permissions should be able to access create form."""
        self.client.force_login(self.profesor)
        response = self.client.get(reverse("reservation_create") + f"?reservableset_slug={self.fri.slug}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'id="reservationForm"')

    def test_profesor_create_valid_reservation(self):
        """Professor should be able to create a valid reservation."""
        self.client.force_login(self.profesor)
        response = self.client.post(
            reverse("reservation_create") + f"?reservableset_slug={self.fri.slug}",
            {
                "start": "2024-06-02T10:00:00",
                "end": "2024-06-02T11:00:00",
                "reason": "Testing form creation",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # Check that a new reservation was created
        self.assertTrue(Reservation.objects.filter(reason="Testing form creation", owners=self.profesor).exists())

    def test_profesor_create_double_reservation_denied(self):
        """Professor without double_reserve permission should not be able to create overlapping reservation."""
        self.client.force_login(self.profesor)
        response = self.client.post(
            reverse("reservation_create") + f"?reservableset_slug={self.fri.slug}",
            {
                "start": "2024-06-03T10:30:00Z",
                "end": "2024-06-03T11:30:00Z",
                "reason": "Testing double booking denial",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id],
            },
        )
        # Should fail and return the form with errors
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form = response.context["form"]
        self.assertTrue(any("No double booking" in str(error) for error in form.non_field_errors()))

    def test_profesor2_create_double_reservation_allowed(self):
        """Professor with double_reserve permission should be able to create overlapping reservation."""
        self.client.force_login(self.profesor2)
        response = self.client.post(
            reverse("reservation_create") + f"?reservableset_slug={self.fri.slug}",
            {
                "start": "2024-06-03T10:30:00Z",
                "end": "2024-06-03T11:30:00Z",
                "reason": "Testing double booking allowed",
                "owners": [self.profesor2.id],
                "reservables": [self.p22.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, getattr(response, "context", None) and response.context["form"].errors)
        # Check that the overlapping reservation was created
        self.assertTrue(
            Reservation.objects.filter(reason="Testing double booking allowed", owners=self.profesor2).exists()
        )

    def test_profesor_create_invalid_time_range(self):
        """Should fail when end time is before start time."""
        self.client.force_login(self.profesor)
        response = self.client.post(
            reverse("reservation_create") + f"?reservableset_slug={self.fri.slug}",
            {
                "start": "2024-06-02T11:00:00",
                "end": "2024-06-02T10:00:00",
                "reason": "Testing invalid time range",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form = response.context["form"]
        self.assertIn("End time must be after start time.", form.errors["end"])

    #
    # EDITING A MULTI-RESERVABLE RESERVATION (regression test)
    #

    def test_edit_reservation_remove_one_reservable_no_crash(self):
        """Removing one reservable from a multi-reservable reservation must not 500.

        Regression test: ReservationForm.clean() never told the permission check which
        reservation was being edited, so the reservation always looked like it was
        overlapping itself, which then crashed instead of denying/allowing the edit.
        """
        self.client.force_login(self.profesor)
        create_response = self.client.post(
            reverse("reservation_create") + f"?reservableset_slug={self.fri.slug}",
            {
                "start": "2024-06-06T10:00:00Z",
                "end": "2024-06-06T11:00:00Z",
                "reason": "Multi-room booking",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id, self.pa.id],
            },
        )
        self.assertEqual(create_response.status_code, status.HTTP_302_FOUND)
        reservation = Reservation.objects.get(reason="Multi-room booking")
        self.assertEqual(reservation.reservables.count(), 2)

        update_response = self.client.post(
            reverse("reservation_update", kwargs={"pk": reservation.pk}),
            {
                "start": "2024-06-06T10:00:00Z",
                "end": "2024-06-06T11:00:00Z",
                "reason": "Multi-room booking",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id],
            },
        )
        self.assertEqual(
            update_response.status_code,
            status.HTTP_302_FOUND,
            getattr(update_response, "context", None) and update_response.context["form"].errors,
        )
        self.assertEqual(list(reservation.reservables.values_list("id", flat=True)), [self.p22.id])

    #
    # RESERVATION UPDATE VIEW
    #

    def test_unauthenticated_update_redirects(self):
        """Unauthenticated user should be redirected to login."""
        response = self.client.get(reverse("reservation_update", kwargs={"pk": self.r1.pk}))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_student_update_reservation_denied(self):
        """Student without permissions should not be able to access update form."""
        self.client.force_login(self.student)
        response = self.client.get(reverse("reservation_update", kwargs={"pk": self.r1.pk}))
        # Student has no change_reservation permission, so should get 403
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_302_FOUND])

    def test_profesor_update_own_reservation_get(self):
        """Professor should be able to access update form for own reservation."""
        self.client.force_login(self.profesor)
        response = self.client.get(reverse("reservation_update", kwargs={"pk": self.r1.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'id="reservationForm"')

    def test_profesor_update_other_reservation_denied(self):
        """Professor should not be able to access update form for other's reservation."""
        self.client.force_login(self.profesor)
        response = self.client.get(reverse("reservation_update", kwargs={"pk": self.r2.pk}))
        # Should be denied because r2 is owned by profesor2
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_302_FOUND])

    def test_profesor_update_own_reservation(self):
        """Professor should be able to update own reservation."""
        self.client.force_login(self.profesor)
        response = self.client.post(
            reverse("reservation_update", kwargs={"pk": self.r1.pk}),
            {
                "start": "2024-06-03T14:00:00Z",
                "end": "2024-06-03T15:00:00Z",
                "reason": "Updated reason",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, getattr(response, "context", None) and response.context["form"].errors)
        # Check that the reservation was updated
        self.r1.refresh_from_db()
        self.assertEqual(self.r1.reason, "Updated reason")

    def test_profesor_update_create_double_reservation_denied(self):
        """Professor without double_reserve should not be able to update to overlapping time."""
        self.client.force_login(self.profesor)
        response = self.client.post(
            reverse("reservation_update", kwargs={"pk": self.r1.pk}),
            {
                "start": "2024-06-04T10:30:00Z",
                "end": "2024-06-04T11:30:00Z",
                "reason": "Trying to create overlap",
                "owners": [self.profesor.id],
                "reservables": [self.pa.id],  # r2 uses pa, so this would overlap
            },
        )
        # Should fail and return the form with errors
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form = response.context["form"]
        self.assertTrue(any("No double booking" in str(error) for error in form.non_field_errors()))
        self.r1.refresh_from_db()
        self.assertEqual(self.r1.reason, "Reservation 1")

    def test_profesor2_update_create_double_reservation_allowed(self):
        """Professor with double_reserve permission should be able to update to overlapping time."""
        self.client.force_login(self.profesor2)
        response = self.client.post(
            reverse("reservation_update", kwargs={"pk": self.r2.pk}),
            {
                "start": "2024-06-03T10:30:00Z",
                "end": "2024-06-03T11:30:00Z",
                "reason": "Double booking allowed",
                "owners": [self.profesor2.id],
                "reservables": [self.p22.id],  # r1 uses p22, so this would overlap
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, getattr(response, "context", None) and response.context["form"].errors)
        # Check that the reservation was updated
        self.r2.refresh_from_db()
        self.assertEqual(self.r2.reason, "Double booking allowed")

    def test_profesor_update_invalid_time_range(self):
        """Should fail when end time is before start time."""
        self.client.force_login(self.profesor)
        response = self.client.post(
            reverse("reservation_update", kwargs={"pk": self.r1.pk}),
            {
                "start": "2024-06-03T15:00:00",
                "end": "2024-06-03T14:00:00",
                "reason": "Invalid time range",
                "owners": [self.profesor.id],
                "reservables": [self.p22.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form = response.context["form"]
        self.assertIn("End time must be after start time.", form.errors["end"])

    #
    # RESERVED-BY DISPLAY
    #

    def test_reservation_detail_shows_owner_name(self):
        """The reservation detail page should show the owner's name, not 'auth.User.None'."""
        self.client.force_login(self.profesor)
        response = self.client.get(reverse("reservation_detail", kwargs={"pk": self.r1.pk}))
        self.assertContains(response, self.profesor.username)
        self.assertNotContains(response, "auth.User.None")
