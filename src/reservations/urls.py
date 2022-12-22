from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from rest_framework import routers

from reservations.views import (  # MyReservationsViewSet,
    NResourcesViewSet,
    ReservableSetViewSet,
    ReservableViewSet,
    ReservationViewSet,
    ResourceViewSet,
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
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("", include("django.contrib.auth.urls")),
]
