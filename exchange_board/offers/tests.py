from django.test import TestCase
from django.urls import reverse
from .models import Offer, Transaction
from .forms import OfferForm
from users.models import CustomUser


class OfferModelTest(TestCase):

    def test_str_representation(self):
        user = CustomUser.objects.create(
            username='testuser',
            referral_code='123ABC'
        )
        offer = Offer.objects.create(
            author=user,
            currency_offered='USD',
            amount_offered=100,
            currency_needed='RUB'
        )
        self.assertEqual(
            str(offer),
            f"{user.username} - 100.00 USD to RUB"
        )


class OfferViewTests(TestCase):

    def test_index_view_displays_offers(self):
        user = CustomUser.objects.create(
            username='testuser',
            referral_code='123ABC'
        )
        Offer.objects.create(
            author=user,
            currency_offered='USD',
            amount_offered=100,
            currency_needed='RUB'
        )
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Currency for sale: 100.00 USD')
        self.assertContains(response, 'Requested currency: RUB')

    def test_offer_creation(self):
        user = CustomUser.objects.create_user(
            username='testuser',
            password='password'
        )
        self.client.login(username='testuser', password='password')

        response = self.client.post(
            reverse('create_offer'),
            {
                'currency_offered': 'USD',
                'amount_offered': 100.00,
                'currency_needed': 'RUB'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Offer.objects.exists())
        self.assertEqual(Offer.objects.first().author, user)


class TransactionModelTest(TestCase):

    def test_str_representation(self):
        user1 = CustomUser.objects.create(
            username='testuser1',
            referral_code='123ABC'
        )
        user2 = CustomUser.objects.create(
            username='testuser2',
            referral_code='456DEF'
        )
        offer = Offer.objects.create(
            author=user1,
            currency_offered='USD',
            amount_offered=100,
            currency_needed='RUB'
        )
        transaction = Transaction.objects.create(
            offer=offer,
            accepting_user=user2
        )
        self.assertEqual(
            str(transaction),
            f"Transaction {offer} - open"
        )


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
            referral_code='456DEF'
        )
        self.offer = Offer.objects.create(
            author=self.user1,
            currency_offered='USD',
            amount_offered=100,
            currency_needed='RUB'
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
        self.assertContains(response, 'Currency Offered: USD')
        self.assertContains(response, 'Amount Offered: 100.00')
        self.assertContains(response, 'Currency Needed: RUB')

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
