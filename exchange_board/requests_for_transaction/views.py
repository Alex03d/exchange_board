from bank_details.forms import BankDetailForm
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from exchange_rates.views import (get_exchange_rate,
                                  get_required_amount_to_be_exchanged,
                                  update_exchange_rates)
from logging_app.loguru_config import logger
from notifications.views import send_acceptance_notification
from offers.forms import OfferForm
from offers.models import IN_PROGRESS, Offer
from requests_for_transaction.forms import RequestForm
from transactions.models import Transaction
from users.views import handshake_count

from .models import RequestForTransaction


@login_required
def create_request_for_transaction(request, offer_id):
    logger.info(f"Создание запроса на транзакцию для предложения с ID {offer_id}")
    offer = get_object_or_404(Offer, id=offer_id)

    if offer.status == IN_PROGRESS:
        messages.error(request, 'This offer is already in progress '
                                'and cannot accept new requests.')
        return redirect('offer_detail', offer_id=offer.id)

    offer_form = OfferForm(user=request.user, instance=offer)

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
                    'New Application for Your Offer',
                    f'User {request.user.username} has submitted an '
                    f'application for your offer. Please check '
                    f'your account for details.',

                    settings.DEFAULT_FROM_EMAIL,
                    [author_email],
                )
                logger.info("Отправка имейла о поступлении"
                            "отклика на офер")

                return redirect('offer_detail', offer_id=offer.id)
            logger.info("Запрос на транзакцию успешно создан")
        else:
            logger.error("Ошибка валидации формы запроса на транзакцию")

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

    return render(
        request,
        'request_for_transaction/request_for_transaction.html',
        context
    )


@login_required
def view_requests_for_transaction(request, request_id):
    requests_for_transaction = RequestForTransaction.objects.filter(
        offer__id=request_id
    ).exclude(status='REJECTED')
    offer = get_object_or_404(Offer, id=request_id)
    if not requests_for_transaction.exists():
        logger.error(f"Запросы на транзакцию для предложения "
                     f"с ID {request_id} не найдены")
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
        applicant = request_for_transaction.applicant
        applicant_code = request_for_transaction.applicant.referral_code
        current_user_code = request.user.referral_code
        handshakes = handshake_count(applicant_code, current_user_code)
        bank_details = request_for_transaction.bank_detail
        aggregated_rating = applicant.aggregated_rating
        applicants_data.append({
            'applicant': request_for_transaction.applicant,
            'referral_code': applicant_code,
            'handshakes': handshakes,
            'handshake_range': range(handshakes),
            'request_for_transaction': request_for_transaction,
            'aggregated_rating': aggregated_rating,
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
        'request_for_transaction/request_for_transaction_detail.html',
        context
    )


@login_required
def accept_request(request, request_id):
    logger.info(f"Принятие запроса на транзакцию с ID {request_id}")
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
        'Your application has been accepted',
        'Your transaction request has been accepted. '
        'Please check the transaction details on the website.',
        settings.DEFAULT_FROM_EMAIL,
        [applicant_email],
        fail_silently=False,
    )
    send_acceptance_notification(request_for_transaction.applicant, offer)

    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def reject_request(request, request_id):
    logger.info(f"Отклонение запроса на транзакцию с ID {request_id}")
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
    # applicant_email = request_for_transaction.applicant.email
    # send_mail(
    #     'Your Application Has Been Declined',
    #     'Unfortunately, the author of the offer has declined your transaction request. '
    #     'It is possible that they found a more suitable counterpart '
    #     'from within their close circle of contacts. However, you can create your own '
    #     'offer to sell currency, and a counterpart for your deal will certainly '
    #     'be found!',
    #     settings.DEFAULT_FROM_EMAIL,
    #     [applicant_email],
    #     fail_silently=False,
    # )

    return redirect('view_requests_for_transaction', request_id=offer.id)


@login_required
def start_transaction(request, offer_id):
    logger.info(f"Начало транзакции для предложения с ID {offer_id}")
    offer = get_object_or_404(Offer, id=offer_id)
    if offer.author == request.user:
        return redirect('index')

    offer.status = IN_PROGRESS
    offer.save()

    transaction, created = Transaction.objects.get_or_create(
        offer=offer,
        accepting_user=request.user
    )
    return redirect('transactions/transaction_detail', transaction_id=transaction.id)
