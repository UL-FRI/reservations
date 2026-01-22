from datetime import datetime
from crispy_forms.layout import Column, Fieldset, Layout, Row, Submit
from dal.autocomplete import ModelSelect2Multiple
from django import forms
from django.core.exceptions import PermissionDenied
from reservations.models import Reservable, Reservation

from crispy_forms.helper import FormHelper
from reservations.permissions import ReservationPermission


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
    # owners = forms.ModelMultipleChoiceField(
    #         queryset=None,
    #         widget=al.widgets.ModelSelect2Multiple(
    #             url='/autocomplete/user/',
    #             attrs={
    #                 'data-placeholder': 'Search for users...',
    #                 'data-minimum-input-length': 1,
    #             },
    #         ),
    #         required=False
    #     )
    reservables = forms.ModelMultipleChoiceField(
        queryset=Reservable.objects.all(),
        widget=ModelSelect2Multiple(
            url='/autocomplete/reservable/',
            attrs={
                'data-placeholder': 'Search for reservables...',
                'data-minimum-input-length': 1,
            },
        ),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = self.request.path
        self.helper.layout = Layout(
            "reason",
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
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        if start and end and start > end:
            self.add_error('end', 'End time must be after start time.')

        try:
            ReservationPermission().can_create_update(cleaned_data, self.request.user)
        except PermissionDenied as e:
            self.add_error(None, str(e))


    class Meta:
        model = Reservation
        exclude = ('requirements',)
