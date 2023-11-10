from django import forms
from .models import TransactionComment


class TransactionCommentForm(forms.ModelForm):
    class Meta:
        model = TransactionComment
        fields = ['content']
