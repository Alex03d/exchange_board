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
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_or_phone = models.CharField(max_length=255, blank=True, null=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_or_phone}"
