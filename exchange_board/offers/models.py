from django.db import models
from django.conf import settings
from django.utils import timezone
from users.models import CustomUser, BankDetail, Currency, CURRENCY_CHOICES

OPEN = 'open'
IN_PROGRESS = 'in progress'
CLOSED = 'closed'
DISPUTE = 'dispute'

STATUS_CHOICES_OFFER = [
    (OPEN, 'Open'),
    ('PENDING', 'Pending'),
    (IN_PROGRESS, 'In Progress'),
    (CLOSED, 'Closed'),
]

STATUS_CHOICES_TRANSACTION = [
    (OPEN, 'Transaction Opened'),
    (IN_PROGRESS, 'In Process'),
    (CLOSED, 'Closed'),
    (DISPUTE, 'Dispute Opened'),
]

YES = 'yes'
NO = 'no'

CONFIRMATION_CHOICES = [
    (YES, 'Yes'),
    (NO, 'No')
]


class ExchangeRate(models.Model):
    usd_to_rub = models.FloatField("USD to RUB")
    mnt_to_rub = models.FloatField("MNT to RUB")
    mnt_to_usd = models.FloatField("MNT to USD")
    date_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def latest(cls):
        return cls.objects.latest('date_updated')

    @staticmethod
    def needs_update():
        try:
            latest = ExchangeRate.latest()
            return latest.date_updated.date() < timezone.now().date()
        except ExchangeRate.DoesNotExist:
            return True


class Offer(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    currency_offered = models.ForeignKey(
        Currency,
        related_name="offers_offered",
        on_delete=models.CASCADE,
    )
    amount_offered = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    currency_needed = models.ForeignKey(
        Currency,
        related_name="offers_needed",
        on_delete=models.CASCADE,
    )
    publishing_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=11,
        choices=STATUS_CHOICES_OFFER,
        default=OPEN
    )
    bank_detail = models.ForeignKey(
        BankDetail,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_offers'
    )

    def __str__(self):
        return (f"{self.author} - {self.amount_offered:.2f} "
                f"{self.currency_offered} to {self.currency_needed}")


class RequestForTransaction(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='requests_for_transaction'
    )
    applicant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('PENDING', 'Pending'),
            ('ACCEPTED', 'Accepted'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    bank_detail = models.ForeignKey(
        BankDetail,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_requests'
    )

    class Meta:
        unique_together = ('offer', 'applicant')

    def __str__(self):
        return (f"Request from {self.applicant} "
                f"for {self.offer} - {self.status}")


class Transaction(models.Model):
    offer = models.OneToOneField(
        Offer,
        on_delete=models.CASCADE,
        related_name='transaction'
    )
    accepting_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accepted_transactions'
    )
    author_asserts_transfer_done = models.CharField(
        max_length=3,
        choices=CONFIRMATION_CHOICES,
        default=NO
    )
    author_uploads_transfer_screenshot = models.ImageField(
        upload_to='screenshots/',
        blank=True,
        null=True
    )
    accepting_user_confirms_money_received = models.CharField(
        max_length=3,
        choices=CONFIRMATION_CHOICES,
        default=NO
    )
    accepting_user_asserts_transfer_done = models.CharField(
        max_length=3,
        choices=CONFIRMATION_CHOICES,
        default=NO
    )
    accepting_user_uploads_transfer_screenshot = models.ImageField(
        upload_to='screenshots/',
        blank=True,
        null=True
    )
    author_confirms_money_received = models.CharField(
        max_length=3,
        choices=CONFIRMATION_CHOICES,
        default=NO
    )
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES_TRANSACTION,
        default=OPEN
    )

    def __str__(self):
        return f"Transaction {self.offer} - {self.status}"
