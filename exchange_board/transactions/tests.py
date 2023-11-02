from django.test import TestCase
from django.urls import reverse
from .models import Offer
from bank_details.models import Currency, BankDetail
from transactions.models import Transaction
from users.models import CustomUser
from exchange_rates.models import ExchangeRate


class TransactionViewTests(TestCase):

    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            username='testuser1',
            password='password1',
            referral_code='123ABC'
        )
        self.user2 = CustomUser.objects.create_user(
            username='testuser2',
            password='password2',
            referral_code='456DEF',
            email="test@email.com",
        )

        usd, created = Currency.objects.get_or_create(code='USD')
        rub, created = Currency.objects.get_or_create(code='RUB')

        self.offer = Offer.objects.create(
            author=self.user1,
            currency_offered=usd,
            amount_offered=50,
            currency_needed=rub
        )

        self.exchange_rate = ExchangeRate.objects.create(
            usd_to_rub=70.00,
            mnt_to_rub=250.00,
            mnt_to_usd=0.035
        )

    def test_start_transaction(self):
        self.client.login(username='testuser2', password='password2')

        response = self.client.get(
            reverse('start_transaction',
                    args=[self.offer.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.exists())

    def test_transaction_detail(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser2', password='password2')

        response = self.client.get(reverse(
            'transaction_detail',
            args=[transaction.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transaction')

    def test_author_uploads_screenshot(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser1', password='password1')

        response = self.client.get(
            reverse('author_uploads_screenshot', args=[transaction.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_accepting_user_uploads_screenshot(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser2', password='password2')

        response = self.client.get(reverse(
            'accepting_user_uploads_screenshot',
            args=[transaction.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_author_confirms_money_received(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser1', password='password1')

        response = self.client.get(reverse(
            'author_confirms_money_received',
            args=[transaction.id])
        )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertEqual(transaction.author_confirms_money_received, 'YES')

    def test_offer_detail_view(self):
        self.client.login(username='testuser1', password='password1')
        response = self.client.get(
            reverse('offer_detail', args=[self.offer.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amount Offered: <strong>50.00 USD</strong>')

    def test_author_upload_screenshot_post(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser1', password='password1')
        with open('media/tests/IMG_3511.PNG', 'rb') as screenshot:
            response = self.client.post(
                reverse('author_uploads_screenshot', args=[transaction.id]),
                {'author_uploads_transfer_screenshot': screenshot}
            )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.author_uploads_transfer_screenshot)

    def test_accepting_user_upload_screenshot_post(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser2', password='password2')
        with open('media/tests/IMG_3511.PNG', 'rb') as screenshot:
            response = self.client.post(
                reverse('accepting_user_uploads_screenshot',
                        args=[transaction.id]),
                {'accepting_user_uploads_transfer_screenshot': screenshot}
            )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.accepting_user_uploads_transfer_screenshot)

    def test_author_asserts_transfer_done(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser1', password='password1')
        response = self.client.get(reverse(
            'author_asserts_transfer_done',
            args=[transaction.id])
        )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertEqual(transaction.author_asserts_transfer_done, 'YES')

    def test_accepting_user_asserts_transfer_done(self):
        transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2
        )
        self.client.login(username='testuser2', password='password2')
        response = self.client.get(reverse(
            'accepting_user_asserts_transfer_done',
            args=[transaction.id])
        )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertEqual(
            transaction.accepting_user_asserts_transfer_done,
            'YES'
        )
