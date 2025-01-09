from django import forms
from django.utils import timezone
from django.contrib.auth.models import User

from .models import MaintenanceSchedule


class GenerateScheduleForm(forms.Form):
    end_date = forms.DateField(
        label="Дата окончания",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d"],
    )

    def clean_end_date(self):
        end_date = self.cleaned_data["end_date"]
        if end_date <= timezone.now().date():
            raise forms.ValidationError(
                "Дата окончания должна быть позже текущей даты."
            )
        return end_date


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class MaintenanceScheduleEditForm(forms.ModelForm):
    class Meta:
        model = MaintenanceSchedule
        fields = ["actual_date", "status", "notes"]
        widgets = {
            "actual_date": forms.DateInput(attrs={"type": "date"}),
        }
