from django.test import TestCase
from django.urls import reverse
from .models import Offer
from bank_details.models import Currency, BankDetail
from users.models import CustomUser
from exchange_rates.models import ExchangeRate


class OfferModelTest(TestCase):

    def test_str_representation(self):
        user = CustomUser.objects.create(
            username='testuser',
            email="test@email.com",
            referral_code='123ABC'
        )

        usd_currency = Currency.objects.get_or_create(code='USD')[0]
        rub_currency = Currency.objects.get_or_create(code='RUB')[0]

        offer = Offer.objects.create(
            author=user,
            currency_offered=usd_currency,
            amount_offered=100,
            currency_needed=rub_currency
        )

        self.assertEqual(
            str(offer),
            f"{user.username} - 100.00 USD to RUB"
        )


class OfferViewTests(TestCase):

    def setUp(self):
        self.exchange_rate = ExchangeRate.objects.create(
            usd_to_rub=70.00,
            mnt_to_rub=250.00,
            mnt_to_usd=0.035
        )

    def test_index_view_displays_offers(self):

        user = CustomUser.objects.create(
            username='testuser',
            referral_code='123ABC'
        )
        user.set_password('password')
        user.save()
        self.client.login(username='testuser', password='password')

        currency_usd = Currency.objects.create(code='USD', name='US Dollar')
        currency_rub = Currency.objects.create(code='RUB', name='Russian Ruble')

        offer = Offer.objects.create(
            author=user,
            currency_offered=currency_usd,
            amount_offered=50,
            currency_needed=currency_rub
        )

        response = self.client.get(reverse('offer_detail', args=[offer.id]))
        self.assertContains(response, 'Amount Offered: <strong>50.00 USD</strong>')

    def test_offer_creation(self):
        user = CustomUser.objects.create_user(
            username='testuser',
            password='password'
        )
        self.client.login(username='testuser', password='password')

        usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            help_text_template='Bank Name for USD transfers'
        )
        rub = Currency.objects.create(code='RUB',
                                      name='Russian Ruble',
                                      help_text_template='Bank Name '
                                                         'for RUB transfers')

        response = self.client.post(
            reverse('create_offer'),
            {
                'currency_offered': usd.id,
                'amount_offered': 500.00,
                'currency_needed': rub.id,
                'selection': 'existing'
            }
        )

        messages = list(response.context['messages'])

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Offer.objects.exists())
        self.assertIn("Limit exceeded for dollars!", str(messages[0]))
        self.assertFalse(Offer.objects.filter(author=user).exists())

    def test_offer_creation_within_limit(self):
        user = CustomUser.objects.create_user(
            username='testuser',
            password='password'
        )
        self.client.login(username='testuser', password='password')

        usd = Currency.objects.create(code='USD',
                                      name='US Dollar',
                                      help_text_template='Bank Name '
                                                         'for USD transfers'
                                      )
        rub = Currency.objects.create(code='RUB', name='Russian Ruble',
                                      help_text_template='Bank Name '
                                                         'for RUB transfers'
                                      )

        bank_detail = BankDetail.objects.create(
            user=user,
            currency=rub,
            bank_name="Test Bank",
            account_or_phone="123456789",
            recipient_name="Test User"
        )

        response = self.client.post(
            reverse('create_offer'),
            {
                'currency_offered': usd.id,
                'amount_offered': 40.00,
                'currency_needed': rub.id,
                'selection': 'existing',
                'bank_detail': bank_detail.id
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Offer.objects.exists())
        self.assertEqual(Offer.objects.first().author, user)
