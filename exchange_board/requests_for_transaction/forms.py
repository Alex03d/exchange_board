from bank_details.models import BankDetail, Currency
from django import forms

from .models import RequestForTransaction


class RequestForm(forms.ModelForm):
    selection = forms.ChoiceField(
        choices=[('new', 'New'), ('existing', 'Existing')],
        widget=forms.RadioSelect,
        initial='new'
    )
    bank_detail = forms.ModelChoiceField(
        queryset=BankDetail.objects.all(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RequestForm, self).__init__(*args, **kwargs)
        self.fields['bank_detail'].widget.attrs.update({'class': 'custom-select'})

        if user:
            self.fields['bank_detail'].queryset = BankDetail.objects.filter(
                user=user
            )

        if self.initial.get('selection') == 'new' or (
                self.data and self.data.get('selection') == 'new'
        ):
            self.fields['bank_detail'].disabled = True

    class Meta:
        model = RequestForTransaction
        fields = ['selection', 'bank_detail']
