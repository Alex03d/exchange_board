from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .forms import UploadScreenshotForm, OfferForm
from .models import Offer, Transaction
from users.views import handshake_count


def index(request):
    offers = Offer.objects.order_by('-publishing_date')[:10]
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

    context = {
        'transaction': transaction,
        'offer': offer,
        'accepting_user': accepting_user,
        'handshakes': handshakes,
        'handshake_range': range(handshakes),
    }

    return render(request, 'transaction_detail.html', context)


@login_required
def offer_detail(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    return render(request, 'offer_detail.html', {'offer': offer})


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

    template_name = ('author_upload_screenshot.html'
                     if user_role == "author"
                     else 'accepting_upload_screenshot.html')
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
    transaction.author_money_confirms_received = 'YES'
    transaction.status = 'CLOSED'
    transaction.save()
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
