from django.conf import settings
from django.db import models
from offers.models import Offer

OPEN = 'open'
IN_PROGRESS = 'in progress'
CLOSED = 'closed'
DISPUTE = 'dispute'

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
