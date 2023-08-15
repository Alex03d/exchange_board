import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('RUB', 'Russian Ruble'),
    ('MNT', 'Mongolian Tugrik'),
]


class CustomUser(AbstractUser):
    # Данные для перевода в рублях
    rub_bank_name = models.CharField(max_length=255, blank=True, null=True, help_text="Bank Name for Ruble transfers")
    rub_account_or_phone = models.CharField(max_length=255, blank=True, null=True, help_text="Account or Phone for Ruble transfers")
    rub_recipient_name = models.CharField(max_length=255, blank=True, null=True, help_text="Recipient Name for Ruble transfers")

    # Данные для перевода в долларах
    usd_bank_name = models.CharField(max_length=255, blank=True, null=True, help_text="Bank Name for USD transfers")
    usd_account_or_phone = models.CharField(max_length=255, blank=True, null=True, help_text="Account or Phone for USD transfers")
    usd_recipient_name = models.CharField(max_length=255, blank=True, null=True, help_text="Recipient Name for USD transfers")

    # Данные для перевода в тугриках
    mnt_bank_name = models.CharField(max_length=255, blank=True, null=True, help_text="Bank Name for Tugrik transfers")
    mnt_account_or_phone = models.CharField(max_length=255, blank=True, null=True, help_text="Account or Phone for Tugrik transfers")
    mnt_recipient_name = models.CharField(max_length=255, blank=True, null=True, help_text="Recipient Name for Tugrik transfers")

    # Пользователь, по чьей ссылке зарегистрирован текущий пользователь
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals")

    # Для отслеживания количества созданных приглашений
    invites_left = models.PositiveSmallIntegerField(default=2)
    referral_code = models.CharField(max_length=255, blank=True, null=True, unique=True,
                                     help_text="Unique referral code for the user.")


class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="invitations_created")
    used = models.BooleanField(default=False)  # Было ли приглашение использовано

    def __str__(self):
        return f"{self.inviter.username}'s invitation - {'Used' if self.used else 'Unused'}"
