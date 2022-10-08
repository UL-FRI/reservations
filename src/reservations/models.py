"""Models for the reservations application."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomSortOrder(models.Model):
    """The model represents users custom sort order.

    TODO: does this makes sense?
    """

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
    """The user profile model."""

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
    """The set of reservables."""

    name = models.CharField(
        max_length=255,
        verbose_name=_("ReservableSet name"),
        help_text=_(
            "ReservableSet model is used to group common reservables together."
        ),
    )
    slug = models.SlugField(unique=True)
    reservables = models.ManyToManyField("Reservable", related_name="reservableset_set")

    def __str__(self) -> str:
        """Return the human readable representation."""
        return self.name


class Resource(models.Model):
    """The model represents a resource a reservable can have."""

    slug = models.SlugField(unique=True)
    type = models.CharField(max_length=255, help_text=_("The type of the resource."))
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        """Return the human readable representation."""
        return self.slug


class NResources(models.Model):
    """Used to represent the number of resources the reservable has."""

    resource = models.ForeignKey("Resource", on_delete=models.CASCADE)
    reservable = models.ForeignKey("Reservable", on_delete=models.CASCADE)
    n = models.IntegerField()

    def __str__(self):
        return "{0} <= {1} x {2}".format(self.reservable, self.resource, self.n)


class Reservable(models.Model):
    """The model represents a thing one can reserve."""

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

    def __str__(self) -> str:
        """Human readable representation."""
        return self.slug


class NRequirements(models.Model):
    """Model represents a requirement a reservation has."""

    resource = models.ForeignKey("Resource", on_delete=models.CASCADE)
    reservation = models.ForeignKey("Reservation", on_delete=models.CASCADE)
    n = models.IntegerField()


class ReservationManager(models.Manager):
    """Custom model manager for reservations."""

    def owned_by_user(self, user) -> models.QuerySet:
        """Get the queryset of reservations (co)owned by the given user."""
        return self.get_query_set().filter(owners=user)

    def prune(self):
        """Delete all reservations."""
        self.get_queryset().filter(reservables=None).delete()


class Reservation(models.Model):
    """A model represent a reservation."""

    reason = models.CharField(
        max_length=255, verbose_name=_("A reason for the reservation.")
    )
    start = models.DateTimeField(verbose_name=_("A start time of the reservation"))
    end = models.DateTimeField(verbose_name=_("An end time of the reservation"))
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("The reservation owners")
    )
    reservables = models.ManyToManyField("Reservable", verbose_name=_("reservables"))
    requirements = models.ManyToManyField(
        "Resource",
        through="NRequirements",
        verbose_name=_("resources"),
        help_text=_("Reservation requirements"),
    )
    objects = ReservationManager()

    class Meta:
        """Add constraints to the database."""

        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_start_before_end",
                check=models.Q(start__lte=models.F("end")),
            )
        ]

    def clean(self):
        """Custom validation."""
        if self.start >= self.end:
            raise ValidationError({"start": "Start date must be before the end date."})

    # Get reservations overlapping in time with the current reservation
    # reserving some of the given reservables. If reservables is not
    # given, self.reservables is used.
    def get_overlapping_reservations(self, reservables=None) -> models.QuerySet:
        """Get a queryset of reservations overlapping with this one."""
        if reservables is None:
            reservables = self.reservables
        return Reservation.objects.filter(
            start__lt=self.end, end__gt=self.start, reservables__in=reservables.all()
        ).exclude(pk=self.pk)

    def __str__(self) -> str:
        """Human readable representation."""
        return self.reason
