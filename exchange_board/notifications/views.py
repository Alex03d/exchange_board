import requests
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from exchange_rates.models import ExchangeRate
from logging_app.loguru_config import logger
from offers.models import Offer


def send_telegram_notification(message):
    logger.info("Отправка сообщения в Telegram")
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": settings.TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(telegram_url, data=data)
    if response.ok:
        logger.info("Сообщение в Telegram успешно отправлено")
    else:
        logger.error("Ошибка при отправке сообщения в Telegram")
    return response.ok


def notify_new_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    domain = get_current_site(request).domain
    offer_url = reverse('offer_detail', kwargs={'offer_id': offer.id})
    offer_link = f"http://{domain}{offer_url}"
    latest_rate = ExchangeRate.latest()
    rub_to_usd = latest_rate.usd_to_rub
    mnt_to_rub = latest_rate.mnt_to_rub
    mnt_to_usd = latest_rate.mnt_to_usd
    message = (
        f"<b>NEW OFFER № {offer.id}!</b> \n\n"
        f"{offer.author.username} <a href='{offer_link}'>sells {offer.amount_offered} {offer.currency_offered} and wants to buy {offer.currency_needed}</a> \n\n"
        f"Approximate exchange rates:\n\n"
        f"1 USD = {rub_to_usd} RUB,\n"
        f"1 RUB = {mnt_to_rub} MNT,\n"
        f"1 USD = {mnt_to_usd} MNT.\n\n"
        f"Click <a href='{offer_link}'>here</a> to check."
    )
    if send_telegram_notification(message):
        logger.info(f"Уведомление о новом предложении с ID {offer_id} успешно отправлено")
        return JsonResponse({"success": True})
    else:
        logger.error(f"Не удалось отправить уведомление о новом предложении с ID {offer_id}")
        return JsonResponse({"success": False})


def send_acceptance_notification(applicant, offer):
    message = (
        f"<b>OFFER № {offer.id} is now IN PROGRESS!</b>\n\n"
        f"{offer.author.username} has accepted the request from {applicant.username}.\n\n"
        "If you have applied for this offer and were not accepted, "
        "you can always create your own currency exchange offer, "
        "and you'll surely find your counterpart!"
    )
    send_telegram_notification(message)
