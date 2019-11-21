# -*- coding: utf-8 -*-
from django.db.models import Model, CharField, SlugField, IntegerField, Manager
from django.db.models import ManyToManyField, OneToOneField, ForeignKey
from django.db.models import DateTimeField, TextField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class CustomSortOrder(Model):
    name = CharField(
        max_length=64,
        help_text=_('Used to separate between custom sort orders.'),
        verbose_name=_('Name of the custom sort order.')
    )
    order = TextField(
        help_text=_('Comma separated List of reservable ids '
                    'that determines its sort order'),
        default=""
    )


class UserProfile(Model):
    user = OneToOneField(
        settings.AUTH_USER_MODEL,
        primary_key=True,
        related_name='reservations_profile'
    )
    sort_order = ForeignKey(
        'CustomSortOrder',
        help_text=_('How reservables should be sorted'),
        verbose_name=_('Users choosen sort order')
    )


class ReservableSet(Model):
    def __str__(self):
        return self.name

    name = CharField(max_length=255)
    slug = SlugField(unique=True)
    reservables = ManyToManyField(
        'Reservable',
        related_name='reservableset_set'
    )


class Resource(Model):
    def __str__(self):
        return self.slug

    slug = SlugField(unique=True)
    type = CharField(max_length=255)
    name = CharField(max_length=255, null=True, blank=True)


class NResources(Model):
    def __str__(self):
        return "{0} <= {1} x {2}".format(self.reservable,
                                         self.resource, self.n)
    resource = ForeignKey('Resource')
    reservable = ForeignKey('Reservable')
    n = IntegerField()


class Reservable(Model):
    def __str__(self):
        return self.slug

    slug = SlugField(unique=True)
    type = CharField(max_length=255)
    name = CharField(max_length=255)
    resources = ManyToManyField('Resource', through='NResources')

    class Meta:
        permissions = (
            ('reserve',
             'Create a reservation using this reservable'),
            ('double_reserve',
             'Create an overlapping reservation'),
            ('manage_reservations',
             'Manage reservations using this reservable'),
        )
        verbose_name = _('reservables')


class NRequirements(Model):
    resource = ForeignKey('Resource')
    reservation = ForeignKey('Reservation')
    n = IntegerField()


class ReservationManager(Manager):
    def owned_by_user(self, user):
        return self.get_query_set().filter(owners=user)

    def prune(self):
        self.get_queryset().filter(reservables=None).delete()


class Reservation(Model):
    def __str__(self):
        return self.reason

    reason = CharField(max_length=255, verbose_name=_('reason'))
    start = DateTimeField(verbose_name=_('start'))
    end = DateTimeField(verbose_name=_('end'))
    owners = ManyToManyField(settings.AUTH_USER_MODEL,
                             verbose_name=_('owners'))
    reservables = ManyToManyField('Reservable', verbose_name=_('reservables'))
    requirements = ManyToManyField('Resource', through='NRequirements',
                                   verbose_name=_('resources'),
                                   help_text=_('Reservation requirements'))
    objects = ReservationManager()

    # custom validation.
    def clean(self):
        if self.start >= self.end:
            raise ValidationError(
                {'start': 'Start date must be before the end date.'}
            )

    # Get reservations overlapping in time with the current reservation
    # reserving some of the given reservables. If reservables is not
    # given, self.reservables is used.
    def get_overlapping_reservations(self, reservables=None):
        if reservables is None:
            reservables = self.reservables
        return Reservation.objects.filter(
            start__lt=self.end, end__gt=self.start,
            reservables__in=reservables.all()
        ).exclude(pk=self.pk)
