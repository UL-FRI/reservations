from django.urls import include, path, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.generic.base import RedirectView

from rest_framework import routers

from reservations.views import (
    NResourcesViewSet,
    ReservableSetViewSet,
    ReservableViewSet,
    OldReservableViewSet,
    OldReservationViewSet,
    ReservationViewSet,
    ResourceViewSet,
    HomeView,
    TimelineView,
    ReservationCreateView,
    ReservationUpdateView
)

router = routers.DefaultRouter()
router.register(r"resources", ResourceViewSet)
router.register(r"reservables", ReservableViewSet)
router.register(r"sets", ReservableSetViewSet)
router.register(r"nresources", NResourcesViewSet)
router.register(r"reservations", ReservationViewSet)


class QueryRedirectView(RedirectView):
    query_string = True
    url = "/api/reservations/"


urlpatterns = [
    path("", HomeView.as_view()),
    path("timeline/<str:reservable_set_slug>/<str:reservable_type_slug>", TimelineView.as_view(), name="timeline"),

    path("reservations/create", ReservationCreateView.as_view(), name="reservation_create"),
    path("reservations/<int:pk>/", ReservationUpdateView.as_view(), name="reservation_update"),

    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),

    # Legacy endpoints
    re_path(r"sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/reservables",
    OldReservableViewSet.as_view({"get": "list"}),),
    path("reservations/", OldReservationViewSet.as_view()),

    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("", include("django.contrib.auth.urls")),
]
