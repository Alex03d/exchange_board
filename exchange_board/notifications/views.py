import requests
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from offers.models import Offer
from exchange_rates.models import ExchangeRate


def send_telegram_notification(message):
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": settings.TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(telegram_url, data=data)
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
        f"NEW OFFER! \n\n"
        f"{offer.author.username} <a href='{offer_link}'>sells {offer.amount_offered} {offer.currency_offered} and wants to buy {offer.currency_needed}</a> \n\n"
        f"Approximate exchange rates:\n\n"
        f"1 USD = {rub_to_usd} RUB,\n"
        f"1 RUB = {mnt_to_rub} MNT,\n"
        f"1 USD = {mnt_to_usd} MNT.\n\n"
        f"Click <a href='{offer_link}'>here</a> to check."
    )
    if send_telegram_notification(message):
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False})
