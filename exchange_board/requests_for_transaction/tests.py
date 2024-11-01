from bank_details.models import BankDetail
from django.test import Client, TestCase
from django.urls import reverse
from exchange_rates.models import ExchangeRate
from offers.models import Currency, Offer
from transactions.models import Transaction
from users.models import CustomUser

from .models import RequestForTransaction


class TransactionRequestTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@mail.com',
            password='12345',
            referral_code='1-1-1',
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            email='otheruser@mail.com',
            password='12345',
            referral_code='1-1-1-1',
        )

        self.currency = Currency.objects.create(name="USD", code="840")
        self.offer = Offer.objects.create(
            author=self.user,
            currency_offered=self.currency,
            amount_offered=100.00,
            currency_needed=self.currency
        )

        self.bank_detail = BankDetail.objects.create(
            user=self.other_user,
            bank_name="Test Bank",
            currency=self.currency
        )

        self.client = Client()

        self.exchange_rate = ExchangeRate.objects.create(
            usd_to_rub=74.50,
            mnt_to_rub=0.025,
            mnt_to_usd=0.00034,
            usd_to_rub_alternative=74.45
        )

    def test_create_request_for_transaction(self):
        self.client.login(username='otheruser', password='12345')
        post_data = {
            'selection': 'existing',
            'bank_detail': self.bank_detail.id,
        }
        response = self.client.post(
            reverse(
                'create_request_for_transaction',
                kwargs={'offer_id': self.offer.id}
            ),
            post_data,
            follow=True
        )
        self.assertRedirects(
            response,
            expected_url=reverse(
                'offer_detail',
                kwargs={'offer_id': self.offer.id}
            )
        )
        self.assertTrue(RequestForTransaction.objects.filter(
            offer=self.offer,
            applicant=self.other_user,
            bank_detail=self.bank_detail
        ).exists())

    def test_view_requests_for_transaction_not_found(self):
        self.client.login(
            username='testuser',
            password='12345'
        )
        response = self.client.get(
            reverse(
                'view_requests_for_transaction',
                kwargs={'request_id': 999}
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_view_requests_for_transaction_forbidden(self):
        self.client.login(username='otheruser', password='12345')
        RequestForTransaction.objects.create(
            offer=self.offer,
            applicant=self.other_user,
            bank_detail=self.bank_detail
        )
        response = self.client.get(
            reverse(
                'view_requests_for_transaction',
                kwargs={'request_id': self.offer.id}
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_accept_request(self):
        self.client.login(username='testuser', password='12345')
        request_for_transaction = RequestForTransaction.objects.create(
            offer=self.offer,
            applicant=self.other_user,
            bank_detail=self.bank_detail
        )
        response = self.client.post(
            reverse(
                'accept_request',
                kwargs={'request_id': request_for_transaction.id}
            )
        )
        self.assertEqual(response.status_code, 302)
        request_for_transaction.refresh_from_db()
        self.assertEqual(request_for_transaction.status, 'ACCEPTED')
        transaction_exists = Transaction.objects.filter(
            offer=self.offer,
            accepting_user=self.other_user
        ).exists()
        self.assertTrue(transaction_exists)

    def test_reject_request(self):
        self.client.login(username='testuser', password='12345')
        request_for_transaction = RequestForTransaction.objects.create(
            offer=self.offer,
            applicant=self.other_user,
            bank_detail=self.bank_detail
        )
        response = self.client.post(
            reverse(
                'reject_request',
                kwargs={'request_id': request_for_transaction.id}
            )
        )
        self.assertEqual(response.status_code, 302)
        request_for_transaction.refresh_from_db()
        self.assertEqual(request_for_transaction.status, 'REJECTED')

    def test_start_transaction(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.post(
            reverse(
                'start_transaction',
                kwargs={'offer_id': self.offer.id}
            )
        )
        self.assertEqual(response.status_code, 302)
        transaction_exists = Transaction.objects.filter(
            offer=self.offer,
            accepting_user=self.other_user
        ).exists()
        self.assertTrue(transaction_exists)
