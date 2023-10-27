from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Exists
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from .forms import (UploadScreenshotForm, OfferForm,
                    BankDetailForm, RequestForm)
from .models import (Offer, Transaction, IN_PROGRESS,
                     CLOSED, RequestForTransaction)
from users.views import handshake_count
from users.models import BankDetail, Currency


def index(request):
    offers_list = Offer.objects.order_by('-publishing_date').annotate(
        has_requests=Exists(RequestForTransaction.objects.filter(
            offer=OuterRef('pk')
        )
        )
    )
    paginator = Paginator(offers_list, 10)

    page = request.GET.get('page')
    offers = paginator.get_page(page)

    context = {
        'offers': offers,
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
    context = {
        'offer': offer,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),
        'user_has_sent_request': user_has_sent_request,
        'requests_for_transaction': requests_for_transaction
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
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def author_asserts_transfer_done(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.offer.author == request.user:
        transaction.author_asserts_transfer_done = 'YES'
        transaction.status = 'IN_PROGRESS'
        transaction.save()
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
        applicants_data.append({
            'applicant': request_for_transaction.applicant,
            'referral_code': applicant_code,
            'handshakes': handshakes,
            'handshake_range': range(handshakes),
            'request_for_transaction': request_for_transaction
        })
    context = {
        'requests_for_transaction': requests_for_transaction,
        'applicants_data': applicants_data,
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

    return redirect('view_requests_for_transaction', request_id=offer.id)
