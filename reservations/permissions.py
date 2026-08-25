"""Base permission class.

Used by Django REST framework.
"""

from typing import Optional

from django.contrib.auth.models import Permission, User
from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.core import ObjectPermissionChecker
from reservations.models import Reservable, Reservation
from reservations.serializers import ReservationSerializer
from reservations.util import ListWithAll
from rest_framework import exceptions, permissions
from rest_framework.request import Request
from rest_framework.views import View


class ReservationPermission(permissions.DjangoModelPermissionsOrAnonReadOnly):
    """Check the permissions when retrieving / modifying objects.

    Both model-level permission and the object-level permission are checked.

    Since the permissions are not checked when creating new models / listing models the
    additional checks have to be performed on the serializer level (creation) and the
    permission filter has to be applied (when listing models).

    Since we always allow read-only access the permission filter is actually currently
    not necessary.
    """

    def can_create_update(
        self, validated_data, user, reservation: Optional[Reservation] = None
    ):
        """Check if the reservation from the given data can be created.

        :raises PermissionDenied: when reservation can not be created / updated.
        """
        reservables = ListWithAll(validated_data.get("reservables", []))
        # Users with manage permission on reservables can always reserve them.
        if self.has_manage_permissions(reservables, user):
            return

        self.check_reservables_permissions(reservables, user)

        start = validated_data["start"]
        end = validated_data["end"]
        overlapping_reservations = Reservation.objects.overlapping(
            start, end, reservables
        )
        if reservation is not None:
            # User has to be owner of the existing reservation in order to modify it.
            if not reservation.owners.filter(pk=user.pk).exists():
                raise exceptions.PermissionDenied(
                    _("Must be owner to modify the resevation.")
                )

            # Remove the existing reservation from the overlapping set.
            overlapping_reservations = overlapping_reservations.exclude(pk=reservation.pk)

        if overlapping_reservations.exists():
            self.can_overlap(overlapping_reservations, reservables, user)

    def has_object_permission(
        self, request: Request, view: View, reservation: Reservation
    ) -> bool:
        """Does user have reserve permissions on the given reservation."""
        # Always allow read-only access, even to unauthenticated users.
        if request.method in permissions.SAFE_METHODS:
            return True

        # The user must be authenticated at this point or has_permission on the parent
        # object would fail.
        serializer = ReservationSerializer(data=request.data, instance=reservation)
        serializer.is_valid(raise_exception=True)
        self.can_create_update(serializer.validated_data, request.user, reservation)
        return True

    def check_reservables_permissions(self, reservables: models.QuerySet | ListWithAll, user):
        """Does user have reserve permissions on all reservables.

        :raise PermissionDenied: when user has no permission on at least one reservable.
        """
        checker = ObjectPermissionChecker(user)
        if any(
            not checker.has_perm("reserve", reservable)
            for reservable in reservables.all()
        ):
            raise exceptions.PermissionDenied(
                detail=_("Insufficient privileges on reservables.")
            )

    def has_manage_permissions(self, reservables: models.QuerySet | ListWithAll, user) -> bool:
        """Does user have manage permissions on all reservables."""
        checker = ObjectPermissionChecker(user)
        return all(
            checker.has_perm("manage_reservations", reservable)
            for reservable in reservables.all()
        )

    def can_overlap(
        self,
        overlapping_reservations: models.QuerySet,
        reservables: models.QuerySet,
        user,
    ):
        """
        Check if user can create the given revervation.

        In case the new reservation is overlapping with existing ones check that the
        user has permission to create overlapping reservations.

        :raises PermissionDenied: when the reservation would overlap with existing ones
            on reservables user has no 'double_reserve' permission on.
        """
        checker = ObjectPermissionChecker(user)
        # We have to check the reservables that are contained in the intersection of
        # the overlapping reservations and given reservables.
        reservables_to_check = (
            Reservable.objects.filter(reservations__in=overlapping_reservations)
            .filter(pk__in=[r.pk for r in reservables.all()])
            .distinct()
        )

        # The iterator is used to not construct all the reservable objects.
        if any(
            not checker.has_perm("double_reserve", reservable)
            for reservable in reservables_to_check.iterator()
        ):
            raise exceptions.PermissionDenied(detail=_("No double booking permission."))
