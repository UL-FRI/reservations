"""Reservation application views."""

from heapq import *

from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, serializers, viewsets

from reservations.filters import (
    NResourcesFilter,
    ReservableFilter,
    ReservableSetFilter,
    ReservationFilter,
    ResourceFilter,
)
from reservations.models import (
    NResources,
    Reservable,
    ReservableSet,
    Reservation,
    Resource,
)
from reservations.permissions import ReservationPermission
from reservations.serializers import (
    ReservableNResourcesSerializer,
    ReservableSerializer,
    ReservableSetSerializer,
    ReservationSerializer,
    ResourceSerializer,
)


class ReservableViewSet(viewsets.ModelViewSet):
    """The reservable viewset."""

    serializer_class = ReservableSerializer
    filterset_class = ReservableFilter
    queryset = Reservable.objects.all()


class ResourceViewSet(viewsets.ModelViewSet):
    """The resource viewset."""

    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    filterset_class = ResourceFilter


class ReservableSetViewSet(viewsets.ModelViewSet):
    """The reservable sets viewset."""

    queryset = ReservableSet.objects.all()
    serializer_class = ReservableSetSerializer
    filterset_class = ReservableSetFilter


class NResourcesViewSet(viewsets.ModelViewSet):
    """The nresources viewset."""

    queryset = NResources.objects.all()
    serializer_class = ReservableNResourcesSerializer
    filterset_class = NResourcesFilter


class ReservationViewSet(viewsets.ModelViewSet):
    """Reservation view set."""

    queryset = Reservation.objects.all()
    permission_classes = (ReservationPermission,)
    filterset_class = ReservationFilter
    serializer_class = ReservationSerializer
