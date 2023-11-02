from unittest.mock import patch

from django.test import TestCase

from .models import ExchangeRate
from .views import (get_exchange_rate, get_required_amount_to_be_exchanged,
                    update_exchange_rates)


class ExchangeRateTests(TestCase):

    @patch('exchange_rates.views.get_exchange_rate')
    def test_update_exchange_rates(self, mock_get_rate):
        mock_get_rate.return_value = 1.5
        update_exchange_rates()
        rate = ExchangeRate.objects.first()
        self.assertEqual(rate.usd_to_rub, 1.5)
        self.assertEqual(rate.mnt_to_rub, 1.5)
        self.assertEqual(rate.mnt_to_usd, 1.5)

    @patch('requests.get')
    def test_get_exchange_rate(self, mock_get):
        mock_get.return_value.json.return_value = {'result': 1.5}
        mock_get.return_value.status_code = 200
        rate = get_exchange_rate("USD", "RUB")
        self.assertEqual(rate, 1.5)

    @patch('exchange_rates.views.ExchangeRate.latest')
    def test_get_required_amount_to_be_exchanged(self, mock_latest):
        mock_latest.return_value = ExchangeRate(usd_to_rub=1.5, mnt_to_rub=2.0, mnt_to_usd=0.5)

        class MockOffer:
            class MockCurrency:
                def __init__(self, name):
                    self.name = name

            def __init__(self, currency_offered_name, currency_needed_name, amount_offered):
                self.currency_offered = self.MockCurrency(currency_offered_name)
                self.currency_needed = self.MockCurrency(currency_needed_name)
                self.amount_offered = amount_offered

        offer = MockOffer("RUB", "USD", 150)
        result = get_required_amount_to_be_exchanged(offer)
        self.assertEqual(result['required_amount'], 100)
