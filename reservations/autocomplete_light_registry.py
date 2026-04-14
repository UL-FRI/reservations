from dal import autocomplete
from django.contrib.auth import get_user_model
from django.db import models
from guardian.shortcuts import get_objects_for_user
from reservations.models import Reservable


class ReservableAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Reservable.objects.all()

        # Only retrieve reservables user can see
        qs = get_objects_for_user(self.request.user, "reserve", qs)

        if self.q:
            qs = qs.filter(models.Q(name__icontains=self.q) | models.Q(slug__icontains=self.q))
        return qs

    def get_result_label(self, result):
        return "{0} ({1})".format(result.slug, result.type)


class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = get_user_model().objects.all()

        if self.q:
            qs = qs.filter(
                models.Q(first_name__icontains=self.q)
                | models.Q(last_name__icontains=self.q)
                | models.Q(username__icontains=self.q)
            )
        return qs

    def get_result_label(self, result):
        return "{0} {1}".format(result.first_name, result.last_name)
