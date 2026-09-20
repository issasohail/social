from django import forms

from settings_app.models import FamilyHarmonySettings
from .models import Person


class PersonForm(forms.ModelForm):
    title = forms.ChoiceField(required=False)
    title_other = forms.CharField(required=False, label='Custom title')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings = FamilyHarmonySettings.current()
        choices = [(value, value) for value in settings.title_options or ['Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Prof', 'Other']]
        self.fields['title'].choices = [('', 'Select title')] + choices
        for field_name, values, label in (
            ('education', settings.education_levels, 'Select education'),
            ('occupation', settings.occupation_options, 'Select occupation'),
            ('employer_or_business', settings.employer_options, 'Select employer or business'),
            ('income_range', settings.income_ranges, 'Select income range'),
        ):
            field = self.fields[field_name]
            current_value = getattr(self.instance, field_name, '') if self.instance else ''
            options = list(values or [])
            if current_value and current_value not in options:
                options.append(current_value)
            field.choices = [('', label)] + [(value, value) for value in options]
        if self.instance and self.instance.title and self.instance.title not in {value for value, _ in choices}:
            self.initial['title'] = 'Other'
            self.initial['title_other'] = self.instance.title

    def clean(self):
        cleaned = super().clean()
        selected_title = cleaned.get('title')
        title_other = (cleaned.get('title_other') or '').strip()
        if selected_title == 'Other':
            cleaned['title'] = title_other or selected_title
        return cleaned

    class Meta:
        model = Person
        exclude = ('full_name', 'normalized_identity_number', 'created_by', 'updated_by', 'created_at', 'updated_at', 'archived_at', 'is_demo')
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}), 'current_address': forms.Textarea(attrs={'rows': 2}), 'permanent_address': forms.Textarea(attrs={'rows': 2}), 'interests': forms.Textarea(attrs={'rows': 2})}
