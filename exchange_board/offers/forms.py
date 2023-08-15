from django import forms
from .models import Transaction, Offer


class UploadScreenshotForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['author_uploads_transfer_screenshot', 'accepting_user_uploads_transfer_screenshot']


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['currency_offered', 'amount_offered', 'currency_needed']
