import random
import string
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True, blank=False)
    is_email_confirmed = models.BooleanField(default=False)

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

    invitation_code_used = models.UUIDField(null=True, blank=True)
    aggregated_rating = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if self.is_superuser and not self.pk:
            last_code = (
                CustomUser.objects.filter(is_superuser=True)
                .order_by('-referral_code')
                .values_list('referral_code', flat=True)
                .first()
            )
            next_code = int(last_code) + 1 if last_code else 1
            self.referral_code = str(next_code)

        super(CustomUser, self).save(*args, **kwargs)


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
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        unique_together = ('user', 'author')


class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    inviter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="invitations_created"
    )
    used = models.BooleanField(default=False)

    invited_user = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitation_used"
    )

    def __str__(self):
        return (f"{self.inviter.username}'s invitation - "
                f"{'Used' if self.used else 'Unused'}")


class EmailConfirmation(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    # confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False)
    confirmation_code = models.CharField(max_length=6, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        super().save(*args, **kwargs)
