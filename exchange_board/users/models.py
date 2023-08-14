import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('RUB', 'Russian Ruble'),
    ('MNT', 'Mongolian Tugrik'),
]


class CustomUser(AbstractUser):
    # Таким образом каждый пользователь имеет 3 поля для хранения данных для переводов по каждой из валют
    rub_transfer_data = models.TextField(blank=True, null=True, help_text="Data for Ruble transfers")
    usd_transfer_data = models.TextField(blank=True, null=True, help_text="Data for USD transfers")
    mnt_transfer_data = models.TextField(blank=True, null=True, help_text="Data for Tugrik transfers")

    # Для отслеживания количества созданных приглашений
    invites_left = models.PositiveSmallIntegerField(default=2)


class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="invitations_created")
    used = models.BooleanField(default=False)  # Было ли приглашение использовано

    def __str__(self):
        return f"{self.inviter.username}'s invitation - {'Used' if self.used else 'Unused'}"
