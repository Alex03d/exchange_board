from bank_details.models import CURRENCY_CHOICES, BankDetail, Currency
from django.conf import settings
from django.db import models

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
