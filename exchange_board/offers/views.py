from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Exists
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from .forms import UploadScreenshotForm, OfferForm
from .models import (Offer, Transaction, OPEN, IN_PROGRESS,
                     CLOSED, DISPUTE, RequestForTransaction)
from users.views import handshake_count


def index(request):
    offers_list = Offer.objects.order_by('-publishing_date').annotate(
        has_requests=Exists(RequestForTransaction.objects.filter(offer=OuterRef('pk'))))
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
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.author = request.user
            offer.save()
            return redirect('offer_detail', offer_id=offer.id)
    else:
        form = OfferForm()

    return render(request, 'offers/create_offer.html', {'form': form})


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
    rfts = RequestForTransaction.objects.filter(offer__id=offer_id)
    context = {
        'offer': offer,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),
        'user_has_sent_request': user_has_sent_request,
        'requests_for_transaction': rfts
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

    RequestForTransaction.objects.create(offer=offer, applicant=request.user)
    return redirect('offer_detail', offer_id=offer.id)


@login_required
def view_requests_for_transaction(request, request_id):
    rfts = RequestForTransaction.objects.filter(offer__id=request_id).exclude(status='REJECTED')
    if not rfts.exists():
        return HttpResponseNotFound('No requests found for this offer. <a href="/">Return to home</a>.')
    if rfts.first().offer.author != request.user:
        return HttpResponseForbidden(
            'You don\'t have permission to perform this action. <a href="/">Return to home</a>.')

    applicants_data = []
    for rft in rfts:
        applicant_code = rft.applicant.referral_code
        current_user_code = request.user.referral_code
        handshakes = handshake_count(applicant_code, current_user_code)
        applicants_data.append({
            'applicant': rft.applicant,
            'referral_code': applicant_code,
            'handshakes': handshakes,
            'handshake_range': range(handshakes),
            'request_for_transaction': rft  # Добавляем объект RequestForTransaction здесь
        })
    context = {
        'requests_for_transaction': rfts,
        'applicants_data': applicants_data,
    }
    return render(request, 'offers/request_for_transaction_detail.html', context)


@login_required
def accept_request(request, request_id):
    rft = get_object_or_404(RequestForTransaction, id=request_id)
    offer = rft.offer

    # Проверка, чтобы только автор предложения мог принять заявку
    if offer.author != request.user:
        return HttpResponseForbidden("You don't have permission to perform this action.")

    # Устанавливаем статус заявки в "ACCEPTED"
    rft.status = 'ACCEPTED'
    rft.save()

    # Начинаем транзакцию
    offer.status = IN_PROGRESS
    offer.save()

    transaction, created = Transaction.objects.get_or_create(
        offer=offer,
        accepting_user=rft.applicant
    )

    # Перенаправляем пользователя на страницу деталей транзакции
    return redirect('transaction_detail', transaction_id=transaction.id)



@login_required
def reject_request(request, request_id):
    rft = get_object_or_404(RequestForTransaction, id=request_id)
    offer = rft.offer

    # Проверка, чтобы только автор предложения мог отклонить заявку
    if offer.author != request.user:
        return HttpResponseForbidden("You don't have permission to perform this action.")

    # Устанавливаем статус заявки в "REJECTED"
    rft.status = 'REJECTED'
    rft.save()

    return redirect('view_requests_for_transaction', request_id=offer.id)
