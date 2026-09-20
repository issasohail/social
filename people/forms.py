from django import forms

from .models import Person


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = ('full_name', 'normalized_identity_number', 'created_by', 'updated_by', 'created_at', 'updated_at', 'archived_at', 'is_demo')
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}), 'current_address': forms.Textarea(attrs={'rows': 2}), 'permanent_address': forms.Textarea(attrs={'rows': 2}), 'interests': forms.Textarea(attrs={'rows': 2})}
