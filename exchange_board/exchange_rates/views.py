import requests

from loguru import logger

from decimal import Decimal
from decouple import config
from .models import ExchangeRate


logger.add("my_log.log", rotation="1 day")


API_KEY = config('EXCHANGE_API_KEY')


def update_exchange_rates():
    usd_to_rub = get_exchange_rate("USD", "RUB")
    mnt_to_rub = get_exchange_rate("RUB", "MNT")
    mnt_to_usd = get_exchange_rate("USD", "MNT")

    if usd_to_rub and mnt_to_rub:
        ExchangeRate.objects.create(usd_to_rub=usd_to_rub, mnt_to_rub=mnt_to_rub, mnt_to_usd=mnt_to_usd)


def get_exchange_rate(base_currency, target_currency):
    logger.info(f"Sending request to API for {base_currency} to {target_currency}")
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
    if offer.currency_offered.name == 'RUB':
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
