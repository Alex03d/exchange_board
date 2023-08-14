# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2', 'rub_transfer_data', 'usd_transfer_data', 'mnt_transfer_data')
