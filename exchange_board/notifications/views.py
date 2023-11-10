import requests
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from offers.models import Offer


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
    message = f"New Offer: <a href='{offer_link}'>{offer}</a> by {offer.author.username}"
    if send_telegram_notification(message):
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False})
