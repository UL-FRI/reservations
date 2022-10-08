"""
Register models in Django admin.
"""

from guardian.admin import GuardedModelAdmin

from django.contrib import admin
from django.contrib.auth.models import Permission

from reservations.models import (
    CustomSortOrder,
    NRequirements,
    NResources,
    Reservable,
    ReservableSet,
    Reservation,
    Resource,
    UserProfile,
)


class StudentAdmin(admin.ModelAdmin):
    filter_horizontal = ("groups",)


class ReservationAdmin(GuardedModelAdmin):
    # This will generate a ModelForm
    # form = al.modelform_factory(Reservation, fields='__all__')
    search_fields = ("reason",)


class ReservableAdmin(admin.ModelAdmin):
    list_filter = ("type", "reservableset_set")


admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Reservable, ReservableAdmin)
admin.site.register(Resource)
admin.site.register(NResources)
admin.site.register(ReservableSet)
admin.site.register(NRequirements)
admin.site.register(Permission)
admin.site.register(CustomSortOrder)
admin.site.register(UserProfile)
