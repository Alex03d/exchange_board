from datetime import timedelta

from django.db import models
from django.utils import timezone


class ExchangeRate(models.Model):
    usd_to_rub = models.FloatField("USD to RUB")
    mnt_to_rub = models.FloatField("MNT to RUB")
    mnt_to_usd = models.FloatField("MNT to USD")
    date_updated = models.DateTimeField(auto_now=True)
    usd_to_rub_alternative = models.FloatField("USD to RUB (alternative)")

    @classmethod
    def latest(cls):
        return cls.objects.latest('date_updated')

    @staticmethod
    def needs_update():
        try:
            latest = ExchangeRate.latest()
            time_since_last_update = timezone.now() - latest.date_updated
            return time_since_last_update > timedelta(hours=12)
        except ExchangeRate.DoesNotExist:
            return True
