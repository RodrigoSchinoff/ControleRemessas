# operacoes/forms.py
from django import forms
from django.forms import inlineformset_factory

from .models import Remessa, RemessaItem, Recebimento
from vendedores.models import Vendedor
from produtos.models import Produto  # (ok manter import, caso use em validações futuras)

TIPO_CHOICES = (
    ('REMESSA', 'REMESSA'),
    ('RECEBIMENTO', 'RECEBIMENTO'),
)


class CabecalhoOperacaoForm(forms.Form):
    seller = forms.ModelChoiceField(queryset=Vendedor.objects.none(), label='Vendedor')
    tipo = forms.ChoiceField(choices=TIPO_CHOICES, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        """
        Passe request.current_org a partir da view:
            form = CabecalhoOperacaoForm(request.GET or None, org=request.current_org)
        """
        org = kwargs.pop('org', None)
        super().__init__(*args, **kwargs)
        if org is not None:
            self.fields['seller'].queryset = Vendedor.objects.filter(organization=org).order_by('name')


class RemessaCabecalhoForm(forms.ModelForm):
    class Meta:
        model = Remessa
        fields = ['date']  # apenas data; obs fora do escopo
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class RemessaItemForm(forms.ModelForm):
    # Usamos CharField + TextInput para aceitar vírgula (formato BR) no front
    qty = forms.CharField(
        label='Qtd',
        widget=forms.TextInput(attrs={'class': 'form-control br-0', 'inputmode': 'numeric'})
    )
    unit_price = forms.CharField(
        label='Preço',
        widget=forms.TextInput(attrs={'class': 'form-control br-2', 'inputmode': 'decimal'})
    )

    class Meta:
        model = RemessaItem
        fields = ['product', 'qty', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
        }


RemessaItemFormSet = inlineformset_factory(
    Remessa,
    RemessaItem,
    form=RemessaItemForm,
    extra=5,
    can_delete=True,
    validate_min=False,
)


class RecebimentoForm(forms.ModelForm):
    # Também como CharField para aceitar vírgula no front
    amount = forms.CharField(
        label='Valor recebido',
        widget=forms.TextInput(attrs={'class': 'form-control br-2', 'inputmode': 'decimal'})
    )

    class Meta:
        model = Recebimento
        fields = ['date', 'amount']  # qtd_equivalente é calculada
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
