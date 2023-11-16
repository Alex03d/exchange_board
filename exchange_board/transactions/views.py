from comments.forms import TransactionCommentForm
from comments.models import TransactionComment
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from exchange_rates.views import get_required_amount_to_be_exchanged
from logging_app.loguru_config import logger
from rating.models import Rating
from requests_for_transaction.models import RequestForTransaction
from users.views import handshake_count

from .forms import UploadScreenshotForm
from .models import CLOSED, Transaction


@login_required
def transaction_detail(request, transaction_id):
    logger.info(f"Детали транзакции с ID {transaction_id} запрашиваются")
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
    required_amount = exchange_data['required_amount']
    existing_rating = Rating.objects.filter(
        transaction=transaction,
        author=request.user
    ).first()

    comments_list = TransactionComment.objects.filter(
        transaction=transaction
    ).order_by('-created_at')
    paginator = Paginator(comments_list, 10)
    page_number = request.GET.get('page')
    comments = paginator.get_page(page_number)

    comment_form = TransactionCommentForm(request.POST or None)
    if request.method == 'POST' and comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.transaction = transaction
        new_comment.author = request.user
        new_comment.save()
        return redirect(
            'transaction_detail',
            transaction_id=transaction_id
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
        'required_amount': required_amount,
        'existing_rating': existing_rating,

        'comments': comments,
        'comment_form': comment_form,
    }
    if (request.user.is_superuser
            or request.user == transaction.offer.author
            or request.user == transaction.accepting_user):
        return render(request, 'transactions/transaction_detail.html', context)
    else:
        logger.error(f"Доступ к деталям транзакции с ID {transaction_id} запрещен")
        return HttpResponseForbidden("You are not allowed to view this transaction.")


@login_required
def upload_screenshot(request, transaction_id, user_role):
    logger.info(f"Загрузка скриншота для транзакции "
                f"с ID {transaction_id}, роль: {user_role}")
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
            logger.info(f"Скриншот для транзакции с "
                        f"ID {transaction_id} успешно загружен")
            form.save()
            return redirect(
                'transaction_detail',
                transaction_id=transaction.id
            )

    else:
        form = UploadScreenshotForm(instance=transaction)

    template_name = ('transactions/author_upload_screenshot.html'
                     if user_role == "author"
                     else 'transactions/accepting_upload_screenshot.html')
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
    logger.info(f"Принимающий пользователь пытается подтвердить "
                f"получение денег для транзакции {transaction_id}")
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.accepting_user != request.user:
        logger.error(
            f"Пользователь {request.user} не имеет права подтвердить "
            f"получение денег для транзакции {transaction_id}")
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )

    transaction.accepting_user_confirms_money_received = 'YES'
    transaction.save()
    # author_email = transaction.offer.author.email
    # send_mail(
    #     'Payment Confirmation',
    #     'The counterparty confirms that the transfer has been made.',
    #     settings.DEFAULT_FROM_EMAIL,
    #     [author_email],
    #     fail_silently=False,
    # )
    logger.info(f"Принимающий пользователь успешно подтвердил получение "
                f"денег для транзакции {transaction_id}")
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def author_confirms_money_received(request, transaction_id):
    logger.info(f"Автор транзакции {transaction_id} пытается "
                f"подтвердить получение денег")
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.author_confirms_money_received = 'YES'
    transaction.status = 'CLOSED'
    transaction.save()

    offer = transaction.offer
    offer.status = CLOSED
    offer.save()

    # accepting_user_email = transaction.accepting_user.email
    # send_mail(
    #     'Payment Confirmation',
    #     'The author of the transaction confirms that the transfer has been completed.',
    #     settings.DEFAULT_FROM_EMAIL,
    #     [accepting_user_email],
    #     fail_silently=False,
    # )
    logger.info(f"Автор транзакции {transaction_id} успешно подтвердил "
                f"получение денег и транзакция закрыта")
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def accepting_user_asserts_transfer_done(request, transaction_id):
    logger.info(
        f"Принимающий пользователь {request.user} пытается утвердить "
        f"выполнение перевода для транзакции {transaction_id}")
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.accepting_user != request.user:
        logger.error(
            f"Пользователь {request.user} не имеет права утвердить "
            f"выполнение перевода для транзакции {transaction_id}")
        return HttpResponseForbidden(
            "You don't have permission to perform this action."
        )
    transaction.accepting_user_asserts_transfer_done = 'YES'
    transaction.save()

    # author_email = transaction.offer.author.email
    # send_mail(
    #     'Payment Confirmation',
    #     'The counterparty asserts that the transfer has been made. '
    #     'Please check and confirm the receipt of funds.',
    #     settings.DEFAULT_FROM_EMAIL,
    #     [author_email],
    #     fail_silently=False,
    # )
    logger.info(
        f"Принимающий пользователь {request.user} успешно утвердил "
        f"выполнение перевода для транзакции {transaction_id}")
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def author_asserts_transfer_done(request, transaction_id):
    logger.info(
        f"Автор транзакции {request.user} заявляет о "
        f"выполнении перевода для транзакции {transaction_id}")
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if transaction.offer.author == request.user:
        transaction.author_asserts_transfer_done = 'YES'
        transaction.status = 'IN_PROGRESS'
        transaction.save()

        # accepting_user_email = transaction.accepting_user.email
        # send_mail(
        #     'Payment Confirmation',
        #     'The author of the transaction asserts that the transfer has been completed. '
        #     'Please check and confirm the receipt of funds.',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [accepting_user_email],
        #     fail_silently=False,
        # )
        logger.info(
            f"Автор транзакции {request.user} успешно утвердил выполнение "
            f"перевода для транзакции {transaction_id}")
    return redirect('transaction_detail', transaction_id=transaction.id)
