from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import OuterRef, Exists
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from .forms import OfferForm, RequestForm
from .models import (Offer, IN_PROGRESS, RequestForTransaction)
from bank_details.models import BankDetail, Currency
from bank_details.forms import BankDetailForm
from users.views import handshake_count
from transactions.models import Transaction
from exchange_rates.models import ExchangeRate
from exchange_rates.views import (update_exchange_rates, get_exchange_rate,
                                  get_required_amount_to_be_exchanged)


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
def start_transaction(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if offer.author == request.user:
        return redirect('index')

    offer.status = IN_PROGRESS
    offer.save()

    transaction, created = Transaction.objects.get_or_create(
        offer=offer,
        accepting_user=request.user
    )
    return redirect('transaction_detail', transaction_id=transaction.id)


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

    context = {
        'offer': offer,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),
        'user_has_sent_request': user_has_sent_request,
        'requests_for_transaction': requests_for_transaction,
        'rub_to_usd': rub_to_usd,
        'mnt_to_rub': mnt_to_rub,
        'mnt_to_usd': mnt_to_usd,
        'required_amount': required_amount
    }
    return render(request, 'offers/offer_detail.html', context)


@login_required
def create_request_for_transaction(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)

    if offer.author == request.user:
        return redirect('index')

    bank_detail_to_use = None

    if request.method == "POST":
        request_form = RequestForm(request.POST, user=request.user)
        bank_detail_form = BankDetailForm(
            request.POST,
            initial={'currency': offer.currency_offered}
        )

        existing_request = RequestForTransaction.objects.filter(
            offer=offer,
            applicant=request.user
        ).first()
        if existing_request:
            messages.error(request, 'You have already '
                                    'responded to this offer.')
            return redirect('offer_detail', offer_id=offer.id)

        if request_form.is_valid():
            selection = request_form.cleaned_data.get('selection')

            if selection == 'new':
                if bank_detail_form.is_valid():
                    new_bank_detail = bank_detail_form.save(commit=False)
                    new_bank_detail.user = request.user
                    new_bank_detail.currency = offer.currency_offered
                    new_bank_detail.save()
                    bank_detail_to_use = new_bank_detail
                    print("POST data:", request.POST)

                else:
                    messages.error(request, 'Invalid bank detail form. '
                                            'Please check the details '
                                            'and try again.')

            elif selection == 'existing':
                selected_bank_detail = request_form.cleaned_data.get(
                    'bank_detail'
                )
                if (selected_bank_detail
                        and selected_bank_detail.user == request.user):
                    bank_detail_to_use = selected_bank_detail
                    print("POST data:", request.POST)

                else:
                    messages.error(request, 'Invalid bank detail selection. '
                                            'Please try again.')

            if bank_detail_to_use:
                RequestForTransaction.objects.create(
                    offer=offer,
                    applicant=request.user,
                    bank_detail=bank_detail_to_use
                )
                author_email = offer.author.email
                send_mail(
                    'Новая заявка на ваше предложение',
                    f'Пользователь {request.user.username} отправил '
                    f'заявку на ваше предложение. Пожалуйста, проверьте '
                    f'ваш аккаунт для деталей.',

                    settings.DEFAULT_FROM_EMAIL,
                    [author_email],
                )

                return redirect('offer_detail', offer_id=offer.id)

    else:
        offer_form = OfferForm(user=request.user)
        bank_detail_form = BankDetailForm(
            initial={'currency': offer.currency_offered}
        )

    context = {
        'bank_detail_form': bank_detail_form,
        'offer_form': offer_form,
        'offer': offer
    }

    return render(request, 'offers/request_for_transaction.html', context)


@login_required
def view_requests_for_transaction(request, request_id):
    requests_for_transaction = RequestForTransaction.objects.filter(
        offer__id=request_id
    ).exclude(status='REJECTED')
    offer = get_object_or_404(Offer, id=request_id)
    if not requests_for_transaction.exists():
        return HttpResponseNotFound(
            'No requests found for this offer. '
            '<a href="/">Return to home</a>.'
        )
    if requests_for_transaction.first().offer.author != request.user:
        return HttpResponseForbidden(
            'You don\'t have permission to perform this action. '
            '<a href="/">Return to home</a>.'
        )

    applicants_data = []
    for request_for_transaction in requests_for_transaction:
        applicant_code = request_for_transaction.applicant.referral_code
        current_user_code = request.user.referral_code
        handshakes = handshake_count(applicant_code, current_user_code)
        bank_details = request_for_transaction.bank_detail
        applicants_data.append({
            'applicant': request_for_transaction.applicant,
            'referral_code': applicant_code,
            'handshakes': handshakes,
            'handshake_range': range(handshakes),
            'request_for_transaction': request_for_transaction,
            'bank_details': (request_for_transaction.bank_detail.bank_name
                             if request_for_transaction.bank_detail else None)
        })

    exchange_data = get_required_amount_to_be_exchanged(offer)
    rub_to_usd = exchange_data['rub_to_usd']
    mnt_to_rub = exchange_data['mnt_to_rub']
    mnt_to_usd = exchange_data['mnt_to_usd']
    required_amount = exchange_data['required_amount']

    context = {
        'requests_for_transaction': requests_for_transaction,
        'applicants_data': applicants_data,
        'rub_to_usd': rub_to_usd,
        'mnt_to_rub': mnt_to_rub,
        'mnt_to_usd': mnt_to_usd,
        'offer': offer,
        'required_amount': required_amount
    }
    return render(
        request,
        'offers/request_for_transaction_detail.html',
        context
    )


@login_required
def accept_request(request, request_id):
    request_for_transaction = get_object_or_404(
        RequestForTransaction,
        id=request_id
    )
    offer = request_for_transaction.offer

    if offer.author != request.user:
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )

    request_for_transaction.status = 'ACCEPTED'
    request_for_transaction.save()

    offer.status = IN_PROGRESS
    offer.save()

    transaction, created = Transaction.objects.get_or_create(
        offer=offer,
        accepting_user=request_for_transaction.applicant
    )
    applicant_email = request_for_transaction.applicant.email
    send_mail(
        'Ваша заявка была принята',
        'Ваша заявка на транзакцию была принята. Пожалуйста, проверьте '
        'детали транзакции на сайте.',
        settings.DEFAULT_FROM_EMAIL,
        [applicant_email],
        fail_silently=False,
    )

    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def reject_request(request, request_id):
    request_for_transaction = get_object_or_404(
        RequestForTransaction,
        id=request_id
    )
    offer = request_for_transaction.offer

    if offer.author != request.user:
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )

    request_for_transaction.status = 'REJECTED'
    request_for_transaction.save()
    applicant_email = request_for_transaction.applicant.email
    send_mail(
        'Ваша заявка была отклонена',
        'К сожалению, автор офера отклонил Вашу заявку на транзакцию. '
        'Возможно, он нашел более подходящего ему контрагента '
        'из близкого круга своих контактов. Однако вы можете создать свой '
        'офер на продажу валюты, и контрагент для Вашей сделки обязательно '
        'найдется!.',
        settings.DEFAULT_FROM_EMAIL,
        [applicant_email],
        fail_silently=False,
    )

    return redirect('view_requests_for_transaction', request_id=offer.id)
