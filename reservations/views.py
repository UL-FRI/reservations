"""Reservation application views."""

from collections import defaultdict
from datetime import datetime
from typing import Optional, override
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django_tomselect.app_settings import TomSelectConfig
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import assign_perm
from reservations.overlaps import annotate_overlaps
from reservations.filters import (NResourcesFilter, ReservableFilter,
                                  ReservableSetFilter, ReservationFilter,
                                  ResourceFilter)
from reservations.forms import ReservationForm
from reservations.models import (NResources, Reservable, ReservableSet, ReservableType,
                                 Reservation, Resource)
from reservations.permissions import ReservationPermission
from reservations.serializers import (ReservableNResourcesSerializer,
                                      ReservableSerializer,
                                      ReservableSetSerializer,
                                      ReservationSerializer,
                                      ResourceSerializer, UserSerializer)
from rest_framework import serializers, viewsets
from rest_framework.permissions import SAFE_METHODS


class UserViewSet(viewsets.ModelViewSet):
	serializer_class = UserSerializer
	queryset = User.objects.all()	


class ReservableViewSet(viewsets.ModelViewSet):
    """The reservable viewset."""

    serializer_class = ReservableSerializer
    filterset_class = ReservableFilter
    queryset = Reservable.objects.all()

class OldReservableViewSet(ReservableViewSet):
    """For compatibility with the old version of reservations"""
    def get_queryset(self):
        return super().get_queryset().filter(reservableset_set__slug=self.kwargs['reservable_set_slug'], type__slug=self.kwargs['reservable_type'])

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

class OldReservationViewSet(RedirectView):
    """For compatibility with the old version of reservations"""

    def get_redirect_url(self, *args, **kwargs):
        query_params = dict(self.request.GET)
        if 'start' in query_params:
            query_params['start__gt'] = query_params.pop('start')
        if 'end' in query_params:
            query_params['end__lt'] = query_params.pop('end')
        query_string = urlencode(query_params)
        return f"/api/reservations?{query_string}"


class TimelineView(TemplateView):
    template_name = "reservations/timeline.html"


class HomeView(ListView):
    model = ReservableSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for rs in context['object_list']:
            rs.types = ReservableType.objects.filter(reservables__reservableset_set=rs).distinct()
        return context

class GiveFormRequestMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class ReservationDetailView(DetailView):
    model = Reservation

    @override
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Grup reservables by type for easier display in the template
        by_type = defaultdict(list)
        for r in self.object.reservables.all():
            by_type[r.type].append(r)
        return ctx | {
            "reservables_by_type": dict(by_type),
            "can_edit": self.request.user.has_perm('reservations.change_reservation', self.object),
        }

# Permission are shared between the create and update views, so they're implemented in the form. This also leads to nicer error messages.

class ReservationCreateView(GiveFormRequestMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    
    def form_valid(self, form):
        messages.success(self.request, _('Reservation created successfully.'))
        resp = super().form_valid(form)
        # User who created the reservation should have permission to edit and delete it
        assign_perm('reservations.change_reservation', self.request.user, self.object)
        assign_perm('reservations.delete_reservation', self.request.user, self.object)
        return resp

    @override
    def get_success_url(self):
        return reverse('reservation_detail', kwargs=dict(pk=self.object.pk))

    def get_initial(self):
        initial = super().get_initial()
        # Copy initial values from GET parameters (for embedded create form)
        if "start" in self.request.GET:
            initial["start"] = datetime.fromisoformat(self.request.GET["start"])
        if "end" in self.request.GET:
            initial["end"] = datetime.fromisoformat(self.request.GET["end"])
        # Set the initial owners to the current user
        initial["owners"] = [self.request.user.id]
        # Set the hidden reservableset field for TomSelect to pick up
        initial["reservableset"] = self.request.GET["reservableset_slug"]
        # Set the initial reservable if given
        if "reservables" in self.request.GET:
            initial["reservables"] = self.request.GET["reservables"]
        return initial

class PermissionDeniedMixin(PermissionRequiredMixin):
    """Always show a permission denied error instead of redirecting to the login page."""

    raise_exception = True

class ReservationUpdateView(GiveFormRequestMixin, PermissionDeniedMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm

    def get_required_permissions(self, request: Optional[HttpRequest] = None) -> list[str]:
        return ['reservations.change_reservation']

    @override
    def get_success_url(self):
        return reverse('reservation_detail', kwargs=dict(pk=self.object.pk))

    def form_valid(self, form):
        messages.success(self.request, _('Reservation updated successfully.'))
        return super().form_valid(form)

class ReservationDeleteView(PermissionDeniedMixin, DeleteView):
    model = Reservation
    permission_required = 'reservations.delete_reservation'
    success_url = "/"  # This is ignored

    @override
    def form_valid(self, form):
        super().form_valid(form)
        return HttpResponse(status=204)

class SelfOrSuperuserRequiredMixin(PermissionDeniedMixin):
    """Restrict access to the URL's own `pk` (or 'me') unless the user is a superuser.

    Used to let a user view their own resources while still allowing admins to view anyone's.
    """

    @override
    def check_permissions(self, request: HttpRequest):
        if self.request.user.is_authenticated and (self.kwargs.get('pk') == 'me' or self.request.user.is_superuser):
            return None
        raise PermissionDenied()


class UserView(SelfOrSuperuserRequiredMixin, DetailView):
    model = User

    @override
    def get_object(self, queryset=None):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class UserReservationsView(SelfOrSuperuserRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/user_reservations.html"
    context_object_name = "reservations"
    paginate_by = 20

    def get_target_user(self) -> User:
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get_queryset(self):
        return (
            Reservation.objects.owned_by_user(self.get_target_user())
            .prefetch_related("reservables")
            .order_by("-start")
        )

    def get_template_names(self):
        if self.request.htmx:
            return ["reservations/user_reservations_table.html"]
        return [self.template_name]

    @override
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reservations"] = annotate_overlaps(context["object_list"])
        context["target_user"] = self.get_target_user()
        return context

def login_redirect(request):
    # If OIDC is configured, redirect to the OIDC login page
    if hasattr(settings, "SOCIAL_AUTH_OIDC_OIDC_ENDPOINT"):
        return RedirectView.as_view(url=reverse('social:begin', kwargs={'backend': 'oidc'}))(request)
    # Otherwise, use the admin login page
    return RedirectView.as_view(url=reverse('login'))(request)

class LegacyBookmarkRedirectView(RedirectView):
	@override
	def get_redirect_url(self, *args, **kwargs) -> str | None:
		return reverse('timeline', kwargs=kwargs)
