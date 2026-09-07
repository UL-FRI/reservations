from typing import override

from django.contrib import admin
from django.contrib.auth.models import Permission
from adminsortable2.admin import SortableAdminMixin
from guardian.admin import GuardedModelAdmin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from import_export.admin import ImportExportMixin

from reservations.merge import merge_reservables
from reservations.models import NRequirements, NResources, Reservable, ReservableSet, ReservableType, Reservation, Resource, UserProfile
from reservations_connect.models import ForeignReservable

class ReservationAdmin(GuardedModelAdmin):
    search_fields = ("reason",)
    list_display = ("reason", "start", "end", "_reservables", "created_at", "updated_at")
    list_filter = ("reservables__type", "reservables__reservableset_set", "start", ("reservables", RelatedDropdownFilter), ("importbatch", RelatedDropdownFilter))
    autocomplete_fields = ("reservables", "owners")
    readonly_fields = ("created_at", "updated_at")

    def _reservables(self, obj):
        return ", ".join(r.name for r in obj.reservables.all())

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("reservables")


class ReservableAdmin(SortableAdminMixin, ImportExportMixin, GuardedModelAdmin):
    search_fields = ("name", "slug")
    list_display = ("order", "name", "type", "_reservablesets")
    list_filter = ("type", "reservableset_set")
    actions = ["merge_reservables"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("reservableset_set")

    def _reservablesets(self, obj):
        return ", ".join(rs.name for rs in obj.reservableset_set.all())

    def merge_reservables(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(request, "Please select at least two reservables to merge.")
            return
        primary = queryset.first()
        merge_reservables(primary, queryset[1:])
        self.message_user(request, f"Merged {queryset.count()} reservables into '{primary.name}'.")

    @override
    def get_actions(self, request):
        actions = super().get_actions(request)
        reservablesets = ReservableSet.objects.all()
        for rs in reservablesets:

            def action(modeladmin, request, queryset, rs=rs):
                for reservable in queryset:
                    rs.reservables.add(reservable)

            action_name = f"add_to_{rs.id}"
            actions[action_name] = (
                action,
                action_name,
                f"Add selected reservables to: {rs.name}",
            )
        return actions

    def get_inlines(self, request, obj):
        # Get all ForeignReservable subclasses that point to this Reservable
        inlines = list(super().get_inlines(request, obj))
        # Get all currently installed models that subclass ForeignReservable
        installed_foreignreservables = ForeignReservable.__subclasses__()
        for _model in installed_foreignreservables:

            class ForeignReservableInline(admin.TabularInline):
                model = _model
                extra = 0
                readonly_fields = ("id",)

            ForeignReservableInline.__name__ = f"{_model.__name__}Inline"
            inlines.append(ForeignReservableInline)
        return inlines


class ReservableSetAdmin(SortableAdminMixin, GuardedModelAdmin):
    filter_horizontal = ("reservables",)


class ReservableTypeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("order", "display_name", "slug", "hidden")


admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Reservable, ReservableAdmin)
# admin.site.register(Resource)
# admin.site.register(NResources)
admin.site.register(ReservableSet, ReservableSetAdmin)
admin.site.register(ReservableType, ReservableTypeAdmin)
# admin.site.register(NRequirements)
admin.site.register(Permission)
# admin.site.register(UserProfile)
