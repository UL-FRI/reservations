"""Reservation application views."""

from heapq import *
from typing import override

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from reservations.forms import ReservationForm
from rest_framework import serializers, viewsets
from django.contrib import messages

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

from guardian.mixins import PermissionRequiredMixin


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

    queryset = Reservation.objects.all().prefetch_related("reservables", "requirements").distinct()
    permission_classes = (ReservationPermission,)
    filterset_class = ReservationFilter
    serializer_class = ReservationSerializer

    def perform_create(self, serializer: serializers.Serializer):
        """Perform additional permission checks.

        The has_object_permission is not called when creating objects so we have to
        perform the necessary permission checks here.

        :raises PermissionDenied: if user has no permission to create the reservation.
        """
        ReservationPermission().can_create_update(
            serializer.validated_data, self.request.user
        )
        return super().perform_create(serializer)


class TimelineView(TemplateView):
    template_name = "reservations/timeline.html"


class HomeView(ListView):
    model = ReservableSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for rs in context['object_list']:
            rs.types = set(rs.reservables.values_list('type', flat=True))
        return context

class GiveFormRequestMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

# Permission are shared between the create and update views, so they're implemented in the form. This also leads to nicer error messages.

class ReservationCreateView(GiveFormRequestMixin, CreateView):
    model = Reservation
    form_class = ReservationForm

    def form_valid(self, form):
        messages.success(self.request, 'Reservation created successfully.')
        return super().form_valid(form)

    @override
    def get_success_url(self):
        return reverse('reservation_update', kwargs=dict(pk=self.object.pk, **self.kwargs))

    def get_initial(self):
        initial = super().get_initial()
        for key, value in self.request.GET.items():
            initial[key] = value
        initial["owners"] = [self.request.user]
        return initial


class ReservationUpdateView(GiveFormRequestMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm

    @override
    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        messages.success(self.request, 'Reservation updated successfully.')
        return super().form_valid(form)
