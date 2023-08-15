# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = (
            'username', 'password1', 'password2',
            'rub_bank_name', 'rub_account_or_phone', 'rub_recipient_name',
            'usd_bank_name', 'usd_account_or_phone', 'usd_recipient_name',
            'mnt_bank_name', 'mnt_account_or_phone', 'mnt_recipient_name'
        )
