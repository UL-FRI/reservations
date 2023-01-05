"""Filters for REST ViewSets in views namespace."""

from django_filters import rest_framework as filters

from reservations.models import (
    NResources,
    Reservable,
    ReservableSet,
    Reservation,
    Resource,
)

# Base lookup types.
NUMBER_LOOKUPS = [
    "exact",
    "in",
    "gt",
    "gte",
    "lt",
    "lte",
    "isnull",
]
TEXT_LOOKUPS = [
    "exact",
    "iexact",
    "contains",
    "icontains",
    "in",
    "startswith",
    "istartswith",
    "isnull",
]
SLUG_LOOKUPS = [
    "exact",
    "in",
]
DATE_LOOKUPS = [
    "exact",
    "gt",
    "gte",
    "lt",
    "lte",
    "isnull",
]
DATETIME_LOOKUPS = DATE_LOOKUPS + [
    "date",
    "time",
]

# Fields available on almost all models.
base_fields = {
    "id": NUMBER_LOOKUPS[:],
    "name": TEXT_LOOKUPS[:],
    "slug": SLUG_LOOKUPS[:],
}


class CheckQueryParamsMixin:
    """Custom query params validation."""

    ALLOWED_ARGUMENTS = (
        "fields",
        "format",
        "limit",
        "offset",
        "ordering",
    )

    def validate_query_parameters(self):
        """Make sure only allowed parameters are used.

        Set user-friendy message along with the list of available arguments on form.
        """
        # Combine parameters obtained from the filters together with the global alowed
        # parameters.
        allowed = set(self.get_filters().keys())
        allowed.update(CheckQueryParamsMixin.ALLOWED_ARGUMENTS)

        given = set(self.request.query_params.keys())

        # Determine the set of not-supported parameters and notify user via form.
        wrong = given - allowed
        if wrong:
            msg = "Wrong parameter(s): {}. Available: {}.".format(
                ", ".join(wrong), ", ".join(allowed)
            )
            self.form.add_error(field=None, error=msg)

    def is_valid(self):
        """Validate the filterset."""
        if self.strict_argument_check:
            self.validate_query_parameters()
        return super().is_valid()


class BaseFilter(CheckQueryParamsMixin, filters.FilterSet):
    """Base filter for all endpoints."""

    # Disable strict query parameters check by setting it to false in derived class.

    # When enabled, unsupported parameters considered error which is reported back to
    # the user.

    strict_argument_check = True

    class Meta:
        """Filter configuration."""


class ReservableFilter(BaseFilter):
    """Reservable filter."""

    class Meta:
        """Set the model and the filterable fields."""

        model = Reservable
        fields = {
            "reservableset_set__slug": SLUG_LOOKUPS,
            "type": TEXT_LOOKUPS,
            "nresources__n": NUMBER_LOOKUPS,
            "nresources__resource__slug": SLUG_LOOKUPS,
            **base_fields,
        }


class ReservationFilter(BaseFilter):
    """Reservation filter."""

    class Meta:
        """Set the model and the filterable fields."""

        model = Reservation
        fields = {
            "reason": TEXT_LOOKUPS,
            "start": DATETIME_LOOKUPS,
            "end": DATETIME_LOOKUPS,
            "owners__first_name": TEXT_LOOKUPS,
            "owners__last_name": TEXT_LOOKUPS,
            "owners__email": TEXT_LOOKUPS,
            "reservables__name": TEXT_LOOKUPS,
            "reservables__slug": SLUG_LOOKUPS,
            "id": NUMBER_LOOKUPS[:],
        }


class ResourceFilter(BaseFilter):
    """Resource filter."""

    class Meta:
        """Set the model and the filterable fields."""

        model = Resource
        fields = {"type": TEXT_LOOKUPS, **base_fields}


class ReservableSetFilter(BaseFilter):
    """Reservable set filter."""

    class Meta:
        """Set the model and the filterable fields."""

        model = ReservableSet
        fields = base_fields


class NResourcesFilter(BaseFilter):
    """NResources filter."""

    class Meta:
        """Set the model and the filterable fields."""

        model = NResources
        fields = {
            "n": NUMBER_LOOKUPS,
            "resource__slug": SLUG_LOOKUPS,
            "resource__name": TEXT_LOOKUPS,
            "reservable__slug": SLUG_LOOKUPS,
            "reservable__name": TEXT_LOOKUPS,
        }
