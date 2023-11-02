from bank_details.models import BankDetail, Currency
from django import forms
from django.core.exceptions import ValidationError
from requests_for_transaction.models import RequestForTransaction

from .models import Offer


class OfferForm(forms.ModelForm):
    selection = forms.ChoiceField(
        choices=[('new', 'New'), ('existing', 'Existing')],
        widget=forms.RadioSelect,
        initial='new'
    )
    bank_detail = forms.ModelChoiceField(
        queryset=BankDetail.objects.all(),
        required=False
    )
    currency_offered = forms.ModelChoiceField(
        queryset=Currency.objects.all()
    )
    currency_needed = forms.ModelChoiceField(
        queryset=Currency.objects.all()
    )

    class Meta:
        model = Offer
        fields = ['currency_offered', 'amount_offered',
                  'currency_needed', 'selection', 'bank_detail']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(OfferForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['bank_detail'].queryset = BankDetail.objects.filter(
                user=user
            )

        if self.initial.get('selection') == 'new' or (
                self.data and self.data.get('selection') == 'new'
        ):
            self.fields['bank_detail'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        currency_offered = cleaned_data.get("currency_offered")
        currency_needed = cleaned_data.get("currency_needed")

        if currency_offered == currency_needed:
            raise ValidationError("Offered currency and needed "
                                  "currency cannot be the same.")

        if currency_offered:
            offered_code = currency_offered.code
            if offered_code == "RUB" and cleaned_data.get(
                    'amount_offered'
            ) > 5000:
                raise ValidationError("Limit exceeded for rubles!")
            elif offered_code == "USD" and cleaned_data.get(
                    'amount_offered'
            ) > 50:
                raise ValidationError("Limit exceeded for dollars!")
            elif offered_code == "MNT" and cleaned_data.get(
                    'amount_offered'
            ) > 150000:
                raise ValidationError("Limit exceeded for tugrugs!")
        return cleaned_data
