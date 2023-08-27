import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('RUB', 'Russian Ruble'),
    ('MNT', 'Mongolian Tugrik'),
]


class CustomUser(AbstractUser):

    rub_bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank Name for Ruble transfers"
    )
    rub_account_or_phone = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Account or Phone for Ruble transfers"
    )
    rub_recipient_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Recipient Name for Ruble transfers"
    )

    usd_bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank Name for USD transfers"
    )
    usd_account_or_phone = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Account or Phone for USD transfers"
    )
    usd_recipient_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Recipient Name for USD transfers"
    )

    mnt_bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank Name for Tugrik transfers"
    )
    mnt_account_or_phone = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Account or Phone for Tugrik transfers"
    )
    mnt_recipient_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Recipient Name for Tugrik transfers"
    )

    invited_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals"
    )

    invites_left = models.PositiveSmallIntegerField(default=3)
    referral_code = models.CharField(max_length=255,
                                     blank=True,
                                     null=True,
                                     unique=True,
                                     help_text=("Unique referral "
                                                "code for the user."))

    def save(self, *args, **kwargs):
        if self.is_superuser:
            last_code = (
                CustomUser.objects.filter(is_superuser=True)
                .order_by('-referral_code')
                .values_list('referral_code', flat=True)
                .first()
            )
            next_code = int(last_code) + 1 if last_code else 1
            self.referral_code = str(next_code)
        super(CustomUser, self).save(*args, **kwargs)


class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inviter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="invitations_created"
    )
    used = models.BooleanField(default=False)

    def __str__(self):
        return (f"{self.inviter.username}'s invitation - "
                f"{'Used' if self.used else 'Unused'}")


class UserFollow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')
