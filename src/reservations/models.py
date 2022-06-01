# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomSortOrder(models.Model):
    name = models.CharField(
        max_length=64,
        help_text=_("Used to separate between custom sort orders."),
        verbose_name=_("Name of the custom sort order."),
    )
    order = models.TextField(
        help_text=_(
            "Comma separated List of reservable ids " "that determines its sort order"
        ),
        default="",
    )


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        primary_key=True,
        related_name="reservations_profile",
        on_delete=models.CASCADE,
    )
    sort_order = models.ForeignKey(
        "CustomSortOrder",
        help_text=_("How reservables should be sorted"),
        verbose_name=_("Users choosen sort order"),
        on_delete=models.CASCADE,
    )


class ReservableSet(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    reservables = models.ManyToManyField("Reservable", related_name="reservableset_set")


class Resource(models.Model):
    def __str__(self):
        return self.slug

    slug = models.SlugField(unique=True)
    type = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)


class NResources(models.Model):
    def __str__(self):
        return "{0} <= {1} x {2}".format(self.reservable, self.resource, self.n)

    resource = models.ForeignKey("Resource", on_delete=models.CASCADE)
    reservable = models.ForeignKey("Reservable", on_delete=models.CASCADE)
    n = models.IntegerField()


class Reservable(models.Model):
    def __str__(self):
        return self.slug

    slug = models.SlugField(unique=True)
    type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    resources = models.ManyToManyField("Resource", through="NResources")

    class Meta:
        permissions = (
            ("reserve", "Create a reservation using this reservable"),
            ("double_reserve", "Create an overlapping reservation"),
            ("manage_reservations", "Manage reservations using this reservable"),
        )
        verbose_name = _("reservables")


class NRequirements(models.Model):
    resource = models.ForeignKey("Resource", on_delete=models.CASCADE)
    reservation = models.ForeignKey("Reservation", on_delete=models.CASCADE)
    n = models.IntegerField()


class ReservationManager(models.Manager):
    def owned_by_user(self, user):
        return self.get_query_set().filter(owners=user)

    def prune(self):
        self.get_queryset().filter(reservables=None).delete()


class Reservation(models.Model):
    def __str__(self):
        return self.reason

    reason = models.CharField(max_length=255, verbose_name=_("reason"))
    start = models.DateTimeField(verbose_name=_("start"))
    end = models.DateTimeField(verbose_name=_("end"))
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_("owners"))
    reservables = models.ManyToManyField("Reservable", verbose_name=_("reservables"))
    requirements = models.ManyToManyField(
        "Resource",
        through="NRequirements",
        verbose_name=_("resources"),
        help_text=_("Reservation requirements"),
    )
    objects = ReservationManager()

    # custom validation.
    def clean(self):
        if self.start >= self.end:
            raise ValidationError({"start": "Start date must be before the end date."})

    # Get reservations overlapping in time with the current reservation
    # reserving some of the given reservables. If reservables is not
    # given, self.reservables is used.
    def get_overlapping_reservations(self, reservables=None):
        if reservables is None:
            reservables = self.reservables
        return Reservation.objects.filter(
            start__lt=self.end, end__gt=self.start, reservables__in=reservables.all()
        ).exclude(pk=self.pk)
