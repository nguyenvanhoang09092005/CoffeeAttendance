from django import forms
from .models import Shift, WeeklyShiftAssignment, ShiftException

class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["name", "start_time", "end_time"]

class WeeklyShiftAssignmentForm(forms.ModelForm):
    class Meta:
        model = WeeklyShiftAssignment
        fields = ["employee", "shift", "weekday"]


class ShiftExceptionForm(forms.ModelForm):
    class Meta:
        model = ShiftException
        fields = ["employee", "shift", "date", "weekday", "start_time", "end_time", "reason", "exception_type", "is_added"]
