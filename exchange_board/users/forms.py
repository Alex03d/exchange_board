# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Rating


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score', 'comment']


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'password1', 'password2',
        )
