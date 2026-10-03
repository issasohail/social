from django import forms
from boards.models import Board
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person
from .models import Portfolio, TeamAppointment, TeamCategory, TeamPosition, Term


def _jk_label(obj):
    lc = obj.local_council
    rc = lc.regional_council if lc else None
    return f'{obj.name} — {lc.name if lc else "—"} — {rc.name if rc else "—"}'


def _person_label(obj):
    phone = obj.whatsapp_number or obj.mobile or 'No phone'
    jk = obj.jamatkhana.name if obj.jamatkhana else 'No JK'
    lc = obj.local_council.name if obj.local_council else 'No LC'
    return f'{obj.full_name} — {phone} — {jk} — {lc}'


class TeamAppointmentForm(forms.ModelForm):
    class Meta:
        model = TeamAppointment
        fields = ['term','board','person','position','portfolio','level','national_council','regional_council','local_council','jamatkhana','covered_jamatkhanas','appointment_date','end_date','is_active','notes']
        widgets = {
            'covered_jamatkhanas': forms.SelectMultiple(),
            'appointment_date': forms.DateInput(attrs={'type':'date'}),
            'end_date': forms.DateInput(attrs={'type':'date'}),
            'notes': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['term'].queryset = Term.objects.filter(is_active=True)
        self.fields['board'].queryset = Board.objects.filter(is_active=True).order_by('sort_order','name')
        self.fields['person'].queryset = Person.objects.filter(is_active=True).select_related('jamatkhana','local_council').order_by('full_name')
        self.fields['person'].label_from_instance = _person_label
        self.fields['position'].queryset = TeamPosition.objects.filter(is_active=True).select_related('category')
        self.fields['portfolio'].queryset = Portfolio.objects.filter(is_active=True).select_related('board')
        self.fields['national_council'].queryset = NationalCouncil.objects.filter(is_active=True).order_by('name')
        self.fields['regional_council'].queryset = RegionalCouncil.objects.filter(is_active=True).select_related('national_council').order_by('name')
        self.fields['local_council'].queryset = LocalCouncil.objects.filter(is_active=True).select_related('regional_council__national_council').order_by('name')
        self.fields['jamatkhana'].queryset = Jamatkhana.objects.filter(is_active=True).select_related('local_council__regional_council').order_by('name')
        self.fields['jamatkhana'].label_from_instance = _jk_label
        self.fields['covered_jamatkhanas'].queryset = Jamatkhana.objects.filter(is_active=True).select_related('local_council__regional_council').order_by('local_council__regional_council__name','local_council__name','name')
        self.fields['covered_jamatkhanas'].label_from_instance = _jk_label
        searchable = ['term','board','person','position','portfolio','level','national_council','regional_council','local_council','jamatkhana','covered_jamatkhanas']
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class','form-control')
            if name in searchable:
                field.widget.attrs['data-searchable'] = 'true'
                field.widget.attrs['data-autofocus-search'] = 'true'

    def clean(self):
        cleaned = super().clean()
        board = cleaned.get('board')
        portfolio = cleaned.get('portfolio')
        if board and portfolio and portfolio.board_id != board.id:
            self.add_error('portfolio', 'Choose a portfolio for the selected board.')
        return cleaned


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name','start_date','end_date','is_current','is_active','notes']
        widgets={'start_date':forms.DateInput(attrs={'type':'date'}),'end_date':forms.DateInput(attrs={'type':'date'}),'notes':forms.Textarea(attrs={'rows':2})}


class TeamCategoryForm(forms.ModelForm):
    class Meta:
        model = TeamCategory
        fields = ['name','sort_order','is_active']


class TeamPositionForm(forms.ModelForm):
    class Meta:
        model = TeamPosition
        fields = ['name','category','sort_order','is_active']

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['category'].queryset = TeamCategory.objects.filter(is_active=True)
        self.fields['category'].widget.attrs['data-searchable'] = 'true'


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['board','name','code','sort_order','is_active']

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['board'].queryset = Board.objects.filter(is_active=True).order_by('sort_order','name')
        self.fields['board'].widget.attrs['data-searchable'] = 'true'
