from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row, Submit
from django import forms
from reservations.models import Reservation
from reservations.permissions import ReservationPermission
from rest_framework.exceptions import PermissionDenied
from django_tomselect.forms import TomSelectModelChoiceField, TomSelectModelMultipleChoiceField
from django_tomselect.app_settings import PluginDropdownHeader, PluginRemoveButton, TomSelectConfig

class FormWithRequestMixin:
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

class ActuallyWorkingDateTimeInput(forms.DateTimeInput):
    """Version of DateTimeInput that can handle JS-style dates"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, attrs={'type': 'datetime-local'})

    def format_value(self, value):
        try:
            value = datetime.fromisoformat(value).strftime('%Y-%m-%dT%H:%M:%S')
        except: pass
        return super().format_value(value)

class ActuallyWorkingDateTimeField(forms.DateTimeField):
    """Version of DateTimeField that uses a proper date input widget."""
    widget = ActuallyWorkingDateTimeInput


class ReservationForm(FormWithRequestMixin, forms.ModelForm):
    start = ActuallyWorkingDateTimeField(label='Start Time')
    end = ActuallyWorkingDateTimeField(label='End Time')
    owners = TomSelectModelMultipleChoiceField(
        help_text="These users will be able to modify this reservation later",
        config=TomSelectConfig(
            url="autocomplete-user",
            value_field="id",
            label_field="full_name",
            placeholder="Search for users...",
            minimum_query_length=1,
            preload="focus",
            close_after_select=True,
            plugin_remove_button=PluginRemoveButton(),
            use_htmx=True,
        )
    )
    reservables = TomSelectModelMultipleChoiceField(
        help_text="Classrooms, teachers or other objects, which this reservation targets",
        config=TomSelectConfig(
            url="autocomplete-reservable",
            value_field="id",
            label_field="name",
            placeholder="Search for reservables...",
            minimum_query_length=1,
            preload="focus",
            close_after_select=True,
            plugin_remove_button=PluginRemoveButton(),
            plugin_dropdown_header=PluginDropdownHeader(
                extra_columns={
                    "type": "Type"
                }
            ),
            use_htmx=True,
        )
    )

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
            self.add_error('end', 'End time must be after start time.')

        # Run permission checks and turn permission errors into form error for display
        try:
            ReservationPermission().can_create_update(cleaned_data, self.request.user)
        except PermissionDenied as e:
            self.add_error(None, str(e))
        
        return cleaned_data


    class Meta:
        model = Reservation
        exclude = ('requirements',)
