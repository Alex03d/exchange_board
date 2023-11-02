from bank_details.models import CURRENCY_CHOICES, BankDetail, Currency
from django.db import models
from offers.models import Offer
from users.models import CustomUser


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
