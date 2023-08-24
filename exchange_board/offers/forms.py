from django import forms
from .models import Transaction, Offer
from django.core.exceptions import ValidationError


class UploadScreenshotForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['author_uploads_transfer_screenshot',
                  'accepting_user_uploads_transfer_screenshot']


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['currency_offered', 'amount_offered', 'currency_needed']

    def clean(self):
        cleaned_data = super().clean()
        currency_offered = cleaned_data.get("currency_offered")
        amount_offered = cleaned_data.get("amount_offered")
        currency_needed = cleaned_data.get("currency_needed")

        if currency_offered == currency_needed:
            raise ValidationError("Offered currency and needed currency cannot be the same.")

        if currency_offered and amount_offered:
            if currency_offered == "RUB" and amount_offered > 5000:
                raise ValidationError("Limit exceeded for rubles!")
            elif currency_offered == "USD" and amount_offered > 50:
                raise ValidationError("Limit exceeded for dollars!")
            elif currency_offered == "MNT" and amount_offered > 150000:
                raise ValidationError("Limit exceeded for tugrugs!")

        return cleaned_data
