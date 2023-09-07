from django.db import models
from django.conf import settings
from users.models import CustomUser


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

CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('RUB', 'Russian Ruble'),
    ('MNT', 'Mongolian Tugrik'),
]

YES = 'yes'
NO = 'no'

CONFIRMATION_CHOICES = [
    (YES, 'Yes'),
    (NO, 'No')
]


class Offer(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    currency_offered = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES
    )
    amount_offered = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    currency_needed = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES
    )
    publishing_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=11,
        choices=STATUS_CHOICES_OFFER,
        default=OPEN
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
