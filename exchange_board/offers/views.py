import requests

from decimal import Decimal
from decouple import config
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import OuterRef, Exists
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import (UploadScreenshotForm, OfferForm,
                    BankDetailForm, RequestForm)
from .models import (Offer, Transaction, IN_PROGRESS,
                     CLOSED, RequestForTransaction, ExchangeRate)
from users.forms import RatingForm
from users.models import BankDetail, Currency, Rating
from users.views import handshake_count


API_KEY = config('EXCHANGE_API_KEY')


def update_exchange_rates():
    usd_to_rub = get_exchange_rate("USD", "RUB")
    mnt_to_rub = get_exchange_rate("RUB", "MNT")
    mnt_to_usd = get_exchange_rate("USD", "MNT")

    if usd_to_rub and mnt_to_rub:
        ExchangeRate.objects.create(usd_to_rub=usd_to_rub, mnt_to_rub=mnt_to_rub, mnt_to_usd=mnt_to_usd)


def get_exchange_rate(base_currency, target_currency):
    API_URL = "https://api.apilayer.com/exchangerates_data/convert"
    headers = {
        "apikey": API_KEY
    }
    params = {
        "from": base_currency,
        "to": target_currency,
        "amount": 1
    }

    response = requests.get(API_URL, headers=headers, params=params)
    response_data = response.json()
    if response.status_code != 200:
        print("Error with status code:", response.status_code)
        print(response.text)
        return None

    return response_data.get("result", None)


def get_required_amount_to_be_exchanged(offer):
    latest_rate = ExchangeRate.latest()
    rub_to_usd = latest_rate.usd_to_rub
    mnt_to_rub = latest_rate.mnt_to_rub
    mnt_to_usd = latest_rate.mnt_to_usd

    required_amount = None
    if offer.currency_offered.name == 'RUR':
        if offer.currency_needed.name == 'USD':
            required_amount = offer.amount_offered / Decimal(rub_to_usd)
        elif offer.currency_needed.name == 'MNT':
            required_amount = offer.amount_offered * Decimal(mnt_to_rub)
    elif offer.currency_offered.name == 'MNT':
        if offer.currency_needed.name == 'RUR':
            required_amount = offer.amount_offered / Decimal(mnt_to_rub)
        elif offer.currency_needed.name == 'USD':
            required_amount = offer.amount_offered / Decimal(mnt_to_usd)
    elif offer.currency_offered.name == 'USD':
        if offer.currency_needed.name == 'RUR':
            required_amount = offer.amount_offered * Decimal(rub_to_usd)
        elif offer.currency_needed.name == 'MNT':
            required_amount = offer.amount_offered * Decimal(mnt_to_usd)

    return {
        'rub_to_usd': rub_to_usd,
        'mnt_to_rub': mnt_to_rub,
        'mnt_to_usd': mnt_to_usd,
        'required_amount': required_amount
    }


def index(request):
    # Обновляем курсы валют при необходимости
    if ExchangeRate.needs_update():
        update_exchange_rates()

    # Получаем последние сохраненные курсы валют из базы данных
    latest_rate = ExchangeRate.latest()
    rub_to_usd = latest_rate.usd_to_rub
    mnt_to_rub = latest_rate.mnt_to_rub
    mnt_to_usd = latest_rate.mnt_to_usd

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
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    offer = transaction.offer
    accepting_user = transaction.accepting_user

    offer_user_code = transaction.offer.author.referral_code
    accepting_user_code = transaction.accepting_user.referral_code
    handshakes = handshake_count(offer_user_code, accepting_user_code)

    offer_bank_detail = offer.bank_detail
    request_for_transaction = RequestForTransaction.objects.filter(
        offer=offer,
        applicant=accepting_user
    ).first()
    accepting_user_bank_detail = (request_for_transaction.bank_detail
                                  if request_for_transaction else None)

    author_not_asserts_paid = (
            transaction.author_asserts_transfer_done == 'no'
    )
    accepting_user_not_confirmed = (
            transaction.accepting_user_confirms_money_received == 'no'
    )
    author_asserts_paid = (
            transaction.author_asserts_transfer_done == 'YES'
    )

    accepting_user_confirmed_but_not_paid_back = (
            transaction.accepting_user_confirms_money_received == 'YES'
            and transaction.author_confirms_money_received == 'no'
            and transaction.accepting_user_asserts_transfer_done == 'no'
    )

    accepting_user_paid_back_author_not_confirmed = (
            transaction.accepting_user_confirms_money_received == 'YES'
            and transaction.author_confirms_money_received == 'no'
            and transaction.accepting_user_asserts_transfer_done == 'YES'
    )

    accepting_user_author_both_confirmed = (
            transaction.accepting_user_confirms_money_received == 'YES'
            and transaction.author_confirms_money_received == 'YES'
    )

    current_user_is_author = (
            request.user == transaction.offer.author
    )
    current_user_is_accepting_user = (
            request.user == transaction.accepting_user
    )

    exchange_data = get_required_amount_to_be_exchanged(offer)
    # rub_to_usd = exchange_data['rub_to_usd']
    # mnt_to_rub = exchange_data['mnt_to_rub']
    # mnt_to_usd = exchange_data['mnt_to_usd']
    required_amount = exchange_data['required_amount']
    existing_rating = Rating.objects.filter(
        transaction=transaction,
        author=request.user
    ).first()

    context = {
        'transaction': transaction,
        'offer': offer,
        'accepting_user': accepting_user,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),

        'accepting_user_not_confirmed': accepting_user_not_confirmed,
        'author_not_asserts_paid': author_not_asserts_paid,
        'author_asserts_paid': author_asserts_paid,

        'accepting_user_confirmed_but_not_paid_back':
            accepting_user_confirmed_but_not_paid_back,
        'accepting_user_paid_back_author_not_confirmed':
            accepting_user_paid_back_author_not_confirmed,
        'accepting_user_author_both_confirmed':
            accepting_user_author_both_confirmed,

        'current_user_is_author': current_user_is_author,
        'current_user_is_accepting_user': current_user_is_accepting_user,
        'offer_bank_detail': offer_bank_detail,
        'accepting_user_bank_detail': accepting_user_bank_detail,
        'required_amount': required_amount,
        'existing_rating': existing_rating,
    }

    return render(request, 'transaction_detail.html', context)


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
def upload_screenshot(request, transaction_id, user_role):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if user_role == "author" and transaction.offer.author != request.user:
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )
    elif (
            user_role == "accepting_user" and
            transaction.accepting_user != request.user
    ):
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )

    if request.method == "POST":
        form = UploadScreenshotForm(
            request.POST,
            request.FILES,
            instance=transaction
        )
        if form.is_valid():
            form.save()
            return redirect(
                'transaction_detail',
                transaction_id=transaction.id
            )

    else:
        form = UploadScreenshotForm(instance=transaction)

    template_name = ('offers/author_upload_screenshot.html'
                     if user_role == "author"
                     else 'offers/accepting_upload_screenshot.html')
    return render(
        request,
        template_name,
        {'form': form, 'transaction': transaction}
    )


def author_uploads_screenshot(request, transaction_id):
    return upload_screenshot(request, transaction_id, "author")


def accepting_user_uploads_screenshot(request, transaction_id):
    return upload_screenshot(request, transaction_id, "accepting_user")


@login_required
def accepting_user_confirms_money_received(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.accepting_user != request.user:
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )

    transaction.accepting_user_confirms_money_received = 'YES'
    transaction.save()
    author_email = transaction.offer.author.email
    send_mail(
        'Утверждение об оплате',
        'Контрагент подтверждает, что перевод был выполнен.',
        settings.DEFAULT_FROM_EMAIL,
        [author_email],
        fail_silently=False,
    )
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def author_confirms_money_received(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.author_confirms_money_received = 'YES'
    transaction.status = 'CLOSED'
    transaction.save()

    offer = transaction.offer
    offer.status = CLOSED
    offer.save()

    accepting_user_email = transaction.accepting_user.email
    send_mail(
        'Подтверждение об оплате',
        'Автор транзакции подтверждает, что перевод был выполнен.',
        settings.DEFAULT_FROM_EMAIL,
        [accepting_user_email],
        fail_silently=False,
    )

    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def accepting_user_asserts_transfer_done(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.accepting_user != request.user:
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )
    transaction.accepting_user_asserts_transfer_done = 'YES'
    transaction.save()

    author_email = transaction.offer.author.email
    send_mail(
        'Утверждение об оплате',
        'Контрагент утверждает, что перевод был выполнен. Пожалуйста, проверьте и подтвердите получение средств.',
        settings.DEFAULT_FROM_EMAIL,
        [author_email],
        fail_silently=False,
    )
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def author_asserts_transfer_done(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.offer.author == request.user:
        transaction.author_asserts_transfer_done = 'YES'
        transaction.status = 'IN_PROGRESS'
        transaction.save()

        accepting_user_email = transaction.accepting_user.email
        send_mail(
            'Утверждение об оплате',
            'Автор транзакции утверждает, что перевод был выполнен. Пожалуйста, проверьте и подтвердите получение средств.',
            settings.DEFAULT_FROM_EMAIL,
            [accepting_user_email],
            fail_silently=False,
        )
    return redirect('transaction_detail', transaction_id=transaction.id)


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
            messages.error(request, 'You have already responded to this offer.')
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
                    'Новая заявка на ваше предложение',  # Тема письма
                    f'Пользователь {request.user.username} отправил заявку на ваше предложение. Пожалуйста, проверьте ваш аккаунт для деталей.',
                    # Содержание письма
                    settings.DEFAULT_FROM_EMAIL,  # Email отправителя
                    [author_email],  # Список получателей
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
            'bank_details': request_for_transaction.bank_detail.bank_name if request_for_transaction.bank_detail else None
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
        'Ваша заявка на транзакцию была принята. Пожалуйста, проверьте детали транзакции на сайте.',
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


def rate_after_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.user == transaction.offer.author:
        author = transaction.offer.author
        recipient = transaction.accepting_user
    else:
        author = transaction.accepting_user
        recipient = transaction.offer.author

    existing_rating = Rating.objects.filter(transaction=transaction, author=author, recipient=recipient).first()

    if request.method == 'POST':
        if existing_rating:
            form = RatingForm(request.POST, instance=existing_rating)
        else:
            form = RatingForm(request.POST)

        if form.is_valid():
            if not existing_rating:
                form.instance.author = author
                form.instance.recipient = recipient

            form.instance.transaction = transaction
            form.save()
            return redirect('transaction_detail', transaction_id=transaction.id)

    else:
        form = RatingForm(instance=existing_rating) if existing_rating else RatingForm()

    return render(request, 'rate_after_transaction.html', {'form': form})
