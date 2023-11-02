from django import forms
from .models import BankDetail


class BankDetailForm(forms.ModelForm):
    class Meta:
        model = BankDetail
        fields = ['bank_name', 'account_or_phone', 'recipient_name']
