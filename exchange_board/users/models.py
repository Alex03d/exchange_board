import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('RUB', 'Russian Ruble'),
    ('MNT', 'Mongolian Tugrik'),
]


class Currency(models.Model):
    code = models.CharField(max_length=3,
                            unique=True,
                            choices=CURRENCY_CHOICES)
    name = models.CharField(max_length=255)
    help_text_template = models.CharField(
        max_length=255,
        help_text="Template for the help text, e.g., "
                  "'Bank Name for {currency_name} transfers'"
    )

    def __str__(self):
        return self.code


class BankDetail(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_or_phone = models.CharField(max_length=255, blank=True, null=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_or_phone}"


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


class EmailConfirmation(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)


class Rating(models.Model):
    transaction = models.ForeignKey('offers.Transaction', on_delete=models.CASCADE, related_name='ratings')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_ratings')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        from offers.models import Transaction
        super(Rating, self).save(*args, **kwargs)
        self.update_user_rating(self.recipient)

    @staticmethod
    def update_user_rating(user):
        ratings = Rating.objects.filter(recipient=user)
        total_score = sum(rating.score for rating in ratings)
        user.aggregated_rating = total_score / ratings.count()
        user.save()
