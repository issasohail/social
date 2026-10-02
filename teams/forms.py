from django import forms
from boards.models import Board
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person
from .models import Portfolio, TeamAppointment, TeamPosition, Term


class TeamAppointmentForm(forms.ModelForm):
    class Meta:
        model = TeamAppointment
        fields = ['term','board','person','position','portfolio','level','national_council','regional_council','local_council','jamatkhana','covered_jamatkhanas','appointment_date','end_date','is_active','notes']
        widgets = {
            'covered_jamatkhanas': forms.SelectMultiple(attrs={'size': 8}),
            'appointment_date': forms.DateInput(attrs={'type':'date'}),
            'end_date': forms.DateInput(attrs={'type':'date'}),
            'notes': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['term'].queryset = Term.objects.filter(is_active=True)
        self.fields['board'].queryset = Board.objects.filter(is_active=True)
        self.fields['person'].queryset = Person.objects.filter(is_active=True).order_by('full_name')
        self.fields['position'].queryset = TeamPosition.objects.filter(is_active=True)
        self.fields['portfolio'].queryset = Portfolio.objects.filter(is_active=True)
        self.fields['national_council'].queryset = NationalCouncil.objects.filter(is_active=True)
        self.fields['regional_council'].queryset = RegionalCouncil.objects.filter(is_active=True)
        self.fields['local_council'].queryset = LocalCouncil.objects.filter(is_active=True)
        self.fields['jamatkhana'].queryset = Jamatkhana.objects.filter(is_active=True)
        self.fields['covered_jamatkhanas'].queryset = Jamatkhana.objects.filter(is_active=True)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','form-control')

class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name','start_date','end_date','is_current','is_active','notes']
        widgets={'start_date':forms.DateInput(attrs={'type':'date'}),'end_date':forms.DateInput(attrs={'type':'date'}),'notes':forms.Textarea(attrs={'rows':2})}

class TeamPositionForm(forms.ModelForm):
    class Meta:
        model = TeamPosition
        fields = ['name','category','sort_order','is_active']

class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['name','code','sort_order','is_active']
