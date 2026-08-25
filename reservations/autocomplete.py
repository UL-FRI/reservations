from django.contrib.auth.models import User
from django.db.models import Value
from django.db.models.functions.text import Concat
from guardian.shortcuts import get_objects_for_user
from reservations.models import Reservable
from django_tomselect.autocompletes import AutocompleteModelView


class ReservableAutocomplete(AutocompleteModelView):
    model = Reservable
    search_lookups = ["name__icontains", "slug__icontains", "type__icontains"]
    value_fields = ["id", "type", "name"]
    filter_by = ["reservableset"]
    ordering = ["type", "order"]
        
    def hook_queryset(self, queryset):
        return get_objects_for_user(self.request.user, "reserve", super().hook_queryset(queryset))


class UserAutocomplete(AutocompleteModelView):
    model = User
    search_lookups = ["first_name__icontains", "last_name__icontains", "username__icontains"]
    virtual_fields = ["full_name"]
    value_fields = ["id"]
    
    def hook_queryset(self, queryset):
        return super().hook_queryset(queryset).annotate(
            full_name=Concat("first_name", Value(" "), "last_name")
        )
