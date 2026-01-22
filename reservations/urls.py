from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from rest_framework import routers

from reservations.views import (  # MyReservationsViewSet,
    NResourcesViewSet,
    ReservableSetViewSet,
    ReservableViewSet,
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
router.register(
    r"sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/reservables",
    ReservableViewSet,
    basename="filtered_reservables",
)


urlpatterns = [
    path("", HomeView.as_view()),
    path("timeline/<str:reservable_set_slug>/<str:reservable_type_slug>", TimelineView.as_view(), name="timeline"),

    path("reservations/create", ReservationCreateView.as_view(), name="reservation_create"),
    path("reservations/<int:pk>/", ReservationUpdateView.as_view(), name="reservation_update"),

    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("", include("django.contrib.auth.urls")),
]
