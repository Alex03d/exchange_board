from bank_details.forms import BankDetailForm
from bank_details.models import BankDetail, Currency
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from exchange_rates.models import ExchangeRate
from exchange_rates.views import (get_exchange_rate,
                                  get_required_amount_to_be_exchanged,
                                  update_exchange_rates)
from requests_for_transaction.models import RequestForTransaction
from notifications.views import notify_new_offer
from users.views import handshake_count

from .forms import OfferForm
from .models import IN_PROGRESS, Offer
from transactions.models import Transaction



def index(request):
    if ExchangeRate.needs_update():
        update_exchange_rates()

    latest_rate = ExchangeRate.latest()
    rub_to_usd = latest_rate.usd_to_rub
    mnt_to_rub = latest_rate.mnt_to_rub
    mnt_to_usd = latest_rate.mnt_to_usd
    usd_to_rub_alternative = latest_rate.usd_to_rub_alternative

    offers_list = Offer.objects.order_by('-publishing_date').annotate(
        has_requests=Exists(RequestForTransaction.objects.filter(
            offer=OuterRef('pk')
        )
        )
    )
    paginator = Paginator(offers_list, 10)
    page = request.GET.get('page')
    offers = paginator.get_page(page)

    if not rub_to_usd or not mnt_to_rub:
        messages.error(request, "Couldn't fetch the exchange rates. "
                                "Some values might be missing.")

    context = {
        'offers': offers,
        'rub_to_usd': rub_to_usd,
        'mnt_to_rub': mnt_to_rub,
        'mnt_to_usd': mnt_to_usd,
        'usd_to_rub_alternative': usd_to_rub_alternative,
    }
    template = 'offers/index.html'

    return render(request, template, context)


@login_required
def create_offer(request):
    bank_details_by_currency = {}

    if request.method == 'POST':
        offer_form = OfferForm(request.POST, user=request.user)

        if offer_form.is_valid():
            currency_needed_code = offer_form.cleaned_data['currency_needed']
            currency_needed = Currency.objects.get(code=currency_needed_code)
            bank_detail_form = BankDetailForm(
                request.POST,
                initial={'currency': currency_needed}
            )

            selection = offer_form.cleaned_data.get('selection')

            if selection == 'new' and bank_detail_form.is_valid():
                new_bank_detail = bank_detail_form.save(commit=False)
                new_bank_detail.user = request.user
                new_bank_detail.currency = currency_needed
                new_bank_detail.save()
                offer = offer_form.save(commit=False)
                offer.bank_detail = new_bank_detail
                offer.author = request.user
                offer.save()
                messages.success(
                    request,
                    'Your offer has been successfully created.'
                )
                return redirect('offer_detail', offer_id=offer.id)

            elif selection == 'existing':
                bank_detail_id = offer_form.cleaned_data.get('bank_detail')
                try:
                    selected_bank_detail_id = bank_detail_id.id if isinstance(
                        bank_detail_id,
                        BankDetail
                    ) else bank_detail_id
                    selected_bank_detail = BankDetail.objects.get(
                        id=selected_bank_detail_id,
                        user=request.user
                    )
                    offer = offer_form.save(commit=False)
                    offer.bank_detail = selected_bank_detail
                    offer.author = request.user
                    offer.save()
                    messages.success(request, 'Your offer has been '
                                              'successfully created.')
                    notify_new_offer(request, offer.id)
                    return redirect('offer_detail',
                                    offer_id=offer.id)
                except BankDetail.DoesNotExist:
                    messages.error(
                        request,
                        'Selected bank detail not found. '
                        'Please check and try again.'
                    )

            else:
                messages.error(
                    request,
                    'There was an error with the bank details. '
                    'Please check and try again.'
                )

        else:
            for error in offer_form.errors.values():
                messages.error(request, error)
            bank_detail_form = BankDetailForm(request.POST)

    else:
        offer_form = OfferForm(user=request.user)
        bank_detail_form = BankDetailForm()

    user_bank_details = BankDetail.objects.filter(user=request.user)
    bank_details_by_currency = {
        detail.currency.code: {
            'bank_name': detail.bank_name,
            'account_or_phone': detail.account_or_phone,
            'recipient_name': detail.recipient_name,
        } for detail in user_bank_details
    }

    return render(request, 'offers/create_offer.html', {
        'form': offer_form,
        'bank_detail_form': bank_detail_form,
        'bank_details_by_currency': bank_details_by_currency,
        'hidden_fields': [],
    })


@login_required
def offer_detail(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    author_code = offer.author.referral_code
    current_user_code = request.user.referral_code
    handshakes = handshake_count(author_code, current_user_code)
    user_has_sent_request = RequestForTransaction.objects.filter(
        applicant=request.user,
        offer=offer
    ).exists()
    requests_for_transaction = RequestForTransaction.objects.filter(
        offer__id=offer_id
    )

    exchange_data = get_required_amount_to_be_exchanged(offer)
    rub_to_usd = exchange_data['rub_to_usd']
    mnt_to_rub = exchange_data['mnt_to_rub']
    mnt_to_usd = exchange_data['mnt_to_usd']
    required_amount = exchange_data['required_amount']

    transaction = None
    try:
        transaction = offer.transaction
    except Transaction.DoesNotExist:
        pass

    context = {
        'offer': offer,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),
        'user_has_sent_request': user_has_sent_request,
        'requests_for_transaction': requests_for_transaction,
        'rub_to_usd': rub_to_usd,
        'mnt_to_rub': mnt_to_rub,
        'mnt_to_usd': mnt_to_usd,
        'required_amount': required_amount,
        'transaction': transaction,
    }
    return render(request, 'offers/offer_detail.html', context)
