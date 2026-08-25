from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row
from django import forms
from reservations.models import Reservation
from reservations.permissions import ReservationPermission
from rest_framework.exceptions import PermissionDenied
from django_tomselect.forms import TomSelectModelMultipleChoiceField
from django_tomselect.app_settings import FilterSpec, PluginDropdownHeader, PluginRemoveButton, TomSelectConfig
from django.utils.translation import gettext_lazy as _

class FormWithRequestMixin:
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

class ActuallyWorkingDateTimeInput(forms.DateTimeInput):
    """Version of DateTimeInput that can handle JS-style dates"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, attrs={'type': 'datetime-local'})

    def format_value(self, value):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime('%Y-%m-%dT%H:%M:%S') if value else ''

class ActuallyWorkingDateTimeField(forms.DateTimeField):
    """Version of DateTimeField that uses a proper date input widget."""
    widget = ActuallyWorkingDateTimeInput


class ReservationForm(FormWithRequestMixin, forms.ModelForm):
    start = ActuallyWorkingDateTimeField(label=_('Start Time'))
    end = ActuallyWorkingDateTimeField(label=_('End Time'))
    owners = TomSelectModelMultipleChoiceField(
        label=_('Owners'),
        help_text=_("These users will be able to modify this reservation later"),
        config=TomSelectConfig(
            url="autocomplete-user",
            value_field="id",
            label_field="full_name",
            placeholder=_("Search for users..."),
            minimum_query_length=1,
            preload="focus",
            close_after_select=True,
            plugin_remove_button=PluginRemoveButton(),
            use_htmx=True,
        )
    )
    reservables = TomSelectModelMultipleChoiceField(
        label=_('Reservables'),
        help_text=_("Classrooms, teachers or other objects, which this reservation targets"),
        config=TomSelectConfig(
            url="autocomplete-reservable",
            value_field="id",
            label_field="name",
            placeholder=_("Search for reservables..."),
            minimum_query_length=1,
            preload="focus",
            close_after_select=True,
            plugin_remove_button=PluginRemoveButton(),
            plugin_dropdown_header=PluginDropdownHeader(
                extra_columns={
                    "type": _("Type")
                }
            ),
            use_htmx=True,
            filter_by=("reservableset", "reservableset_set__slug")
        )
    )
    reservableset = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "reservationForm"
        self.helper.form_action = self.request.path
        self.helper.layout = Layout(
            Field("reason", autofocus=1),
            Row(
                Column("start"),
                Column("end"),
            ),
            "reservableset",
            "owners",
            "reservables",
        )
        # Disable inline media - we'll load it in the wrapping template
        self.helper.include_media = False
    

    def clean(self):
        cleaned_data = super().clean()
        
        # Check end > start
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        if start and end and start > end:
            self.add_error('end', _('End time must be after start time.'))

        # Run permission checks and turn permission errors into form error for display.
        # Skip this when start/end failed validation above: add_error() removes them
        # from cleaned_data, and can_create_update() requires both to be present.
        if 'start' not in cleaned_data or 'end' not in cleaned_data:
            return cleaned_data

        # self.instance is unsaved (pk is None) when creating, so only pass it as the
        # existing reservation when we're actually updating one.
        existing_reservation = self.instance if self.instance and self.instance.pk else None
        try:
            ReservationPermission().can_create_update(cleaned_data, self.request.user, existing_reservation)
        except PermissionDenied as e:
            self.add_error(None, str(e))
        
        return cleaned_data


    class Meta:
        model = Reservation
        exclude = ('requirements',)
