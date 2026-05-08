"""
Register models in Django admin.
"""

from django.contrib import admin
from django.contrib.admin.widgets import (FilteredSelectMultiple,
                                          RelatedFieldWidgetWrapper)
from django.contrib.auth.models import Permission
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from guardian.admin import GuardedModelAdmin
from reservations.models import (NRequirements, NResources, Reservable,
                                 ReservableSet, Reservation, Resource,
                                 UserProfile)


class StudentAdmin(admin.ModelAdmin):
    filter_horizontal = ("groups",)


class ReservationAdmin(GuardedModelAdmin):
    search_fields = ("reason",)
    list_display = ("reason", "start", "end", "_reservables",)
    list_filter = ("reservables__type", "reservables__reservableset_set", "importbatch")
    raw_id_fields = ("reservables", "owners",)

    def _reservables(self, obj):
        return ", ".join(r.name for r in obj.reservables.all())

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("reservables")


class ReservableAdmin(GuardedModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type", "reservableset_set")


class ReservableSetAdmin(GuardedModelAdmin):
    filter_horizontal = ('reservables',)


admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Reservable, ReservableAdmin)
admin.site.register(Resource)
admin.site.register(NResources)
admin.site.register(ReservableSet, ReservableSetAdmin)
admin.site.register(NRequirements)
admin.site.register(Permission)
admin.site.register(UserProfile)
