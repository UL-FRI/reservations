from django.conf.urls import url, include
from django.views.i18n import JavaScriptCatalog
from django_js_reverse.views import  urls_js
from rest_framework import routers
from reservations.views import ResourceViewSet, ReservationViewSet, MyReservationsViewSet 
from reservations.views import ReservableViewSet, ReservableSetViewSet, reservable_set_list_view
from reservations.views import reservable_type_list_view, reservable_resource_view, time_view
from reservations.views import FilteredReservableViewSet


router = routers.DefaultRouter()
router.register(r'resources', ResourceViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/my_reservations',
                MyReservationsViewSet, base_name='my_reservation')
router.register(r'reservables', ReservableViewSet)
router.register(r'sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/reservables',
                FilteredReservableViewSet, base_name='filtered_reservables')
router.register(r'sets', ReservableSetViewSet)


urlpatterns = [
    url(r'^$', reservable_set_list_view, name='reservable_set_list_view'),
    url(r'^types/(?P<reservable_type>[\w-]+)$', reservable_type_list_view, name='reservable_type_list_view'),
    url(r'^sets/(?P<reservable_set_slug>[\w-]+)$', reservable_type_list_view, name='reservable_type_list_view'),
    url(r'^sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/reservable_resources$',
        reservable_resource_view, name='reservable_resource_view'),
    url(r'^sets/(?P<reservable_set_slug>[\w-]+)/types/(?P<reservable_type>[\w-]+)/time_view$',
        time_view, name='time_view'),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^jsi18n/reservations/$',
        JavaScriptCatalog.as_view(packages=['reservations']),
        name='javascript-catalog'),
    url(r'^jsreverse/$', urls_js, name='js_reverse'),
    url('^', include('django.contrib.auth.urls')),
]
