from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Fieldset, Layout, Row, Submit
from dal.autocomplete import ModelSelect2Multiple
from django import forms
from django.contrib.auth.models import User
from reservations.models import Reservable, Reservation
from reservations.permissions import ReservationPermission
from rest_framework.exceptions import PermissionDenied


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
    owners = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=ModelSelect2Multiple(
            url='/autocomplete/user/',
            attrs={
                'data-placeholder': 'Search for users...',
                'data-minimum-input-length': 1,
            },
        ),
        required=True
    )
    reservables = forms.ModelMultipleChoiceField(
        queryset=Reservable.objects.all(),
        widget=ModelSelect2Multiple(
            url='/autocomplete/reservable/',
            attrs={
                'data-placeholder': 'Search for reservables...',
                'data-minimum-input-length': 1,
            },
        ),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = self.request.path
        self.helper.layout = Layout(
            Field("reason", autofocus=1),
            Row(
                Column("start"),
                Column("end"),
            ),
            "owners",
            "reservables",
            Submit('submit', 'Submit')
        )
    

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
