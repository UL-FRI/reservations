"""
Created on Jun 17, 2014

@author: gregor
"""

from autocomplete_light import shortcuts as al
from guardian.shortcuts import get_objects_for_user

from django.conf import settings
from django.contrib.auth import get_user_model

from reservations.models import Reservable, Reservation

#
# autocomplete_light.register(Reservable,
#     search_fields=['name',],
#     attrs={
#         'placeholder': 'Other model name ?',
#         'data-autocomplete-minimum-characters': 1,
#     },
#     widget_attrs={
#         'data-widget-maximum-values': 40,
#         'class': 'modern-style',
#     },
# )


class ReservableAutocomplete(al.AutocompleteModelBase):
    search_fields = ["slug", "name"]
    model = Reservable
    widget_attrs = {"data-widget-maximum-values": 30}

    def choices_for_request(self):
        if not self.request.user.is_staff:
            self.choices = get_objects_for_user(
                self.request.user, "reserve", self.choices
            )
            # Only retrieve reservables user can see
        return super(ReservableAutocomplete, self).choices_for_request()

    def choice_label(self, choice):
        return "{0} ({1})".format(choice.slug, choice.type)


al.register(Reservable, ReservableAutocomplete)


class UserAutocomplete(al.AutocompleteModelBase):
    search_fields = ["first_name", "last_name", "username"]
    model = get_user_model()
    widget_attrs = {"data-widget-maximum-values": 30}

    def choice_label(self, choice):
        return "{0} {1}".format(choice.first_name, choice.last_name)


al.register(get_user_model(), UserAutocomplete)
