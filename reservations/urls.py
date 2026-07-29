from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from reservations.autocomplete import ReservableAutocomplete, UserAutocomplete
from reservations.views import (HomeView, NResourcesViewSet,
                                OldReservableViewSet, OldReservationViewSet,
                                ReservableSetViewSet, ReservableViewSet,
                                ReservationCreateView, ReservationDetailView, ReservationUpdateView,
                                ReservationViewSet, ResourceViewSet,
                                TimelineView, UserViewSet, login_redirect)
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"resources", ResourceViewSet)
router.register(r"reservables", ReservableViewSet)
router.register(r"sets", ReservableSetViewSet)
router.register(r"nresources", NResourcesViewSet)
router.register(r"reservations", ReservationViewSet)


class QueryRedirectView(RedirectView):
    query_string = True
    url = "/api/reservations/"


urlpatterns = [
    # Mostly-static pages
    path("", HomeView.as_view()),
    path("timeline/<str:reservable_set_slug>/<str:reservable_type_slug>", TimelineView.as_view(), name="timeline"),

    # Reservation management form
    path("reservations/create", ReservationCreateView.as_view(), name="reservation_create"),
    path("reservations/<int:pk>/", ReservationDetailView.as_view(), name="reservation_detail"),
    path("reservations/<int:pk>/edit", ReservationUpdateView.as_view(), name="reservation_update"),

    # Autocomplete views
    path('autocomplete/user/',UserAutocomplete.as_view(),name='autocomplete-user'),
    path('autocomplete/reservable/',ReservableAutocomplete.as_view(),name='autocomplete-reservable'),

    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),

    # Legacy endpoints
    re_path(r"sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/reservables",
    OldReservableViewSet.as_view({"get": "list"}),),
    path("reservations/", OldReservationViewSet.as_view()),

    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("autologin/", login_redirect, name="autologin"),
    path("accounts/", include("django.contrib.auth.urls")),

    path("", include("reservations_connect.metronik.urls"), name="metronik_debug"),
]
