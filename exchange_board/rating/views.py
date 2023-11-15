from django.shortcuts import get_object_or_404, redirect, render
from transactions.models import Transaction

from .forms import RatingForm
from .models import Rating

from logging_app.loguru_config import logger

def rate_after_transaction(request, transaction_id):
    logger.info(f"Начало процесса оценки для транзакции с ID {transaction_id}")
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.user == transaction.offer.author:
        author = transaction.offer.author
        recipient = transaction.accepting_user
    else:
        author = transaction.accepting_user
        recipient = transaction.offer.author

    existing_rating = Rating.objects.filter(
        transaction=transaction,
        author=author,
        recipient=recipient
    ).first()

    if request.method == 'POST':
        if existing_rating:
            form = RatingForm(request.POST, instance=existing_rating)
        else:
            form = RatingForm(request.POST)

        if form.is_valid():
            logger.info(f"Форма оценки для транзакции с ID {transaction_id} "
                        f"валидна, сохранение рейтинга")
            if not existing_rating:
                form.instance.author = author
                form.instance.recipient = recipient

            form.instance.transaction = transaction
            form.save()
            return redirect(
                'transaction_detail',
                transaction_id=transaction.id
            )
        else:
            logger.error(f"Ошибка валидации формы оценки "
                         f"для транзакции с ID {transaction_id}")

    else:
        form = RatingForm(
            instance=existing_rating
        ) if existing_rating else RatingForm()

    logger.info("Отображение формы для оценки после транзакции")
    return render(
        request,
        'rating/rate_after_transaction.html',
        {'form': form}
    )
