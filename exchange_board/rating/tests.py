from bank_details.models import Currency
from django.test import RequestFactory, TestCase
from django.urls import reverse
from offers.models import Offer
from transactions.models import NO, OPEN, Transaction
from users.models import CustomUser

from .models import Rating
from .views import rate_after_transaction


class RateAfterTransactionViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.user1 = CustomUser.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass'
        )

        self.currency1 = Currency.objects.create(
            code='USD',
            name='US Dollar',
            help_text_template='Bank Name for USD transfers'
        )
        self.currency2 = Currency.objects.create(
            code='RUB',
            name='Russian Ruble',
            help_text_template='Bank Name for RUB transfers'
        )

        self.offer = Offer.objects.create(
            author=self.user1,
            currency_offered=self.currency1,
            amount_offered=100,
            currency_needed=self.currency2
        )

        self.transaction = Transaction.objects.create(
            offer=self.offer,
            accepting_user=self.user2,
            author_asserts_transfer_done=NO,
            accepting_user_confirms_money_received=NO,
            accepting_user_asserts_transfer_done=NO,
            author_confirms_money_received=NO,
            status=OPEN
        )

    def test_rate_after_transaction_POST_new_rating(self):
        request = self.factory.post(reverse(
            'rate_after_transaction',
            args=[self.transaction.id]),
            data={
            'score': 5,
            'comment': 'Great transaction!'
        })
        request.user = self.user1

        response = rate_after_transaction(
            request,
            transaction_id=self.transaction.id
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Rating.objects.filter(
            transaction=self.transaction,
            author=self.user1,
            recipient=self.user2
        ).exists()
                        )
