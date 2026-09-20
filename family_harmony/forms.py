from django import forms

from .models import FamilyHarmonyPreference, FamilyHarmonyProfile


class FamilyHarmonyProfileForm(forms.ModelForm):
    class Meta:
        model = FamilyHarmonyProfile
        exclude = ('person', 'assigned_officer', 'created_at', 'updated_at', 'is_demo', 'consent_reviewed')
        widgets = {'family_background': forms.Textarea(attrs={'rows': 2}), 'family_values': forms.Textarea(attrs={'rows': 2}), 'personality': forms.Textarea(attrs={'rows': 2}), 'health_information': forms.Textarea(attrs={'rows': 2}), 'personal_statement': forms.Textarea(attrs={'rows': 2}), 'expectations': forms.Textarea(attrs={'rows': 2}), 'notes': forms.Textarea(attrs={'rows': 2})}


class FamilyHarmonyPreferenceForm(forms.ModelForm):
    class Meta:
        model = FamilyHarmonyPreference
        exclude = ('profile',)
        widgets = {'preferred_family_values': forms.Textarea(attrs={'rows': 2}), 'preferred_personality': forms.Textarea(attrs={'rows': 2}), 'other_expectations': forms.Textarea(attrs={'rows': 2}), 'free_text_seeking_description': forms.Textarea(attrs={'rows': 2})}
