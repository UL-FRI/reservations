from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from rest_framework import routers

from reservations.views import (
    FilteredReservableViewSet,
    MyReservationsViewSet,
    ReservableSetViewSet,
    ReservableViewSet,
    ReservationViewSet,
    ResourceViewSet,
    reservable_resource_view,
    reservable_set_list_view,
    reservable_type_list_view,
    time_view,
)

router = routers.DefaultRouter()
router.register(r"resources", ResourceViewSet)
router.register(r"reservations", ReservationViewSet)
router.register(
    r"sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/my_reservations",
    MyReservationsViewSet,
    basename="my_reservation",
)
router.register(r"reservables", ReservableViewSet)
router.register(
    r"sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/reservables",
    FilteredReservableViewSet,
    basename="filtered_reservables",
)
router.register(r"sets", ReservableSetViewSet)


urlpatterns = [
    path("", reservable_set_list_view, name="reservable_set_list_view"),
    path(
        "types/<str:reservable_type>",
        reservable_type_list_view,
        name="reservable_type_list_view",
    ),
    path(
        "sets/<str:reservable_set_slug>",
        reservable_type_list_view,
        name="reservable_type_list_view",
    ),
    path(
        "sets/(<str:reservable_set_slug>/types/<str:reservable_type>/reservable_resources",
        reservable_resource_view,
        name="reservable_resource_view",
    ),
    path(
        "sets/<str:reservable_set_slug>/types/<str:reservable_type>/time_view",
        time_view,
        name="time_view",
    ),
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path(
        "jsi18n/reservations/",
        JavaScriptCatalog.as_view(packages=["reservations"]),
        name="javascript-catalog",
    ),
    path("", include("django.contrib.auth.urls")),
]
