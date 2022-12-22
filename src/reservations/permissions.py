"""Base permission class.

Used by Django REST framework.
"""

from guardian.core import ObjectPermissionChecker

from rest_framework import exceptions, permissions

from reservations.models import Reservable, Reservation
from reservations.serializers import ReservationSerializer


class ReservationPermission(permissions.BasePermission):

    """
    Return modified (by user) object or raise exception if serializer
    data is invalid.
    Return tupple object, reservables.
    Return None, None if no object is
    """

    def get_modified_object(self, request, instance=None):
        obj, reservables = None, None
        if len(request.data) != 0:
            serializer = ReservationSerializer(data=request.data, instance=instance)
            if serializer.is_valid():
                reservables = Reservable.objects.filter(
                    id__in=request.data.getlist("reservables")
                )
                obj = serializer.object
        return obj, reservables

    def get_model_instance_from_kwargs(self, kwargs):
        """
        Return a Reservation instance if 'pk' in contained in kwargs and
        there exists a database object with
        this primary key, None otherwise.
        """
        instance = None
        try:
            pk = kwargs.get("pk", None)
            if pk is not None:
                instance = Reservation.objects.get(pk=pk)
        finally:
            return instance

    def has_permission(self, request, view):
        # Allow safe methods for everybody
        if request.method in permissions.SAFE_METHODS:
            return True

        # Unauthenticated and anonymous users have no acces to
        # unsafe methods
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == "POST":
            obj, reservables = self.get_modified_object(request)

            # Always show add form for new objects
            if obj is None:
                return True
            return self.has_reservables_permissions(
                reservables, request.user
            ) and self.has_overlapping_permissions(obj, reservables, request.user)
        else:
            # For delete and put has_object_permissions will be called
            return True

    def has_object_permission(self, request, view, obj):
        # method: GET, PUT, DELETE
        if request.method in permissions.SAFE_METHODS:
            return True
        u = request.user
        if not u:
            raise exceptions.PermissionDenied(detail=_("Please login"))

        instance = Reservation.objects.get(pk=obj.pk)
        modified_obj, reservables = self.get_modified_object(request, instance)
        if modified_obj is None:
            modified_obj = obj
            reservables = obj.reservables

        # Users with manage permission on reservables can do anything
        if self.has_manage_permissions(reservables, u):
            return True

        return (
            u in obj.owners.all()
            and self.has_reservables_permissions(reservables, u)
            and self.has_overlapping_permissions(modified_obj, reservables, u)
        )

    def has_reservables_permissions(self, reservables, user):
        checker = ObjectPermissionChecker(user)
        for r in reservables.all():
            if not checker.has_perm("reserve", r):
                raise exceptions.PermissionDenied(detail=_("Insufficient privileges"))
        return True

    def has_manage_permissions(self, reservables, user):
        checker = ObjectPermissionChecker(user)
        for r in reservables.all():
            if not checker.has_perm("manage_reservations", r):
                return False
        return True

    def has_overlapping_permissions(self, reservation, reservables, user):
        # do NOT use method on reservation object! It checks
        # object.reservations which does not exist when called from
        # method has_permission.
        overlapping = reservation.overlapping_reservations(reservables)
        checker = ObjectPermissionChecker(user)
        for res in overlapping:
            for r in res.reservables.all():
                if r in (
                    reservables.all() and not checker.has_perm("double_reserve", r)
                ):
                    raise exceptions.PermissionDenied(
                        detail=_("Double booking not allowed")
                    )
        return True
