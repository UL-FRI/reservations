"""

===============
Reservatons app
===============

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReservationsConfig(AppConfig):
    """Reservations config."""

    name = "reservations"
    verbose_name = _("Reservations")
