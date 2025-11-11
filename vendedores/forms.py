# vendedores/forms.py
from django import forms
from .models import Vendedor

class VendedorForm(forms.ModelForm):
    class Meta:
        model = Vendedor
        fields = ['name', 'contact', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'autofocus': True}),
        }
