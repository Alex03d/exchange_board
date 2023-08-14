from django import forms
from .models import Transaction


class UploadScreenshotForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['author_uploads_transfer_screenshot', 'accepting_user_uploads_transfer_screenshot']
