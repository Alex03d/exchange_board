from decimal import Decimal

import requests
from decouple import config
from logging_app.loguru_config import logger

from .models import ExchangeRate

API_KEY = config('EXCHANGE_API_KEY')
ALTERNATIVE_API_KEY = config('CURRENCY_LAYER_API_KEY')


def update_exchange_rates():
    logger.info("Обновление обменных курсов начато")
    usd_to_rub = get_exchange_rate("USD", "RUB")
    mnt_to_rub = get_exchange_rate("RUB", "MNT")
    mnt_to_usd = get_exchange_rate("USD", "MNT")
    usd_to_rub_alternative = get_exchange_rate_from_alternative_api("usd", "rub")

    if usd_to_rub and mnt_to_rub:
        ExchangeRate.objects.create(
            usd_to_rub=usd_to_rub,
            mnt_to_rub=mnt_to_rub,
            mnt_to_usd=mnt_to_usd,
            usd_to_rub_alternative=usd_to_rub_alternative
        )
        logger.info("Обновление обменных курсов завершено")
    else:
        logger.error("Не завершено обновление обменных курсов")


def get_exchange_rate(base_currency, target_currency):
    logger.info(f"Отправка АПИ запроса курса {base_currency} к {target_currency}")
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
        logger.error(
            f"Ошибка API при запросе {base_currency} "
            f"к {target_currency}: {response.status_code}"
        )
        return None
    logger.info(f"Получен курс обмена для {base_currency} к "
                f"{target_currency}: {response_data.get('result', None)}")
    return response_data.get("result", None)


def get_exchange_rate_from_alternative_api(base_currency, target_currency):
    logger.info(
        f"Отправка альтернативного API запроса курса"
        f"{base_currency} к {target_currency}"
    )

    API_URL = (f"https://cdn.jsdelivr.net/gh/fawazahmed0/"
               f"currency-api@1/latest/currencies/{base_currency}/"
               f"{target_currency}.json")

    response = requests.get(API_URL)
    try:
        response_data = response.json()
    except requests.exceptions.JSONDecodeError:
        logger.error(
            f"Failed to decode JSON from response "
            f"for {base_currency} to {target_currency}"
        )
        return 0

    if response.status_code != 200 or 'error' in response_data:
        logger.error(f"Error with status code: {response.status_code}")
        logger.error(response.text)
        return 0

    rate = response_data['rub']

    return rate


def get_required_amount_to_be_exchanged(offer):
    latest_rate = ExchangeRate.latest()
    if not latest_rate:
        logger.error("Ошибка: не удалось получить последние курсы обмена валют")
        return None
    rub_to_usd = latest_rate.usd_to_rub
    mnt_to_rub = latest_rate.mnt_to_rub
    mnt_to_usd = latest_rate.mnt_to_usd
    logger.info(f"Расчет требуемой суммы обмена для предложения: {offer}")

    required_amount = None
    if offer.currency_offered.name == 'RUB':
        if offer.currency_needed.name == 'USD':
            required_amount = offer.amount_offered / Decimal(rub_to_usd)
        elif offer.currency_needed.name == 'MNT':
            required_amount = offer.amount_offered * Decimal(mnt_to_rub)
    elif offer.currency_offered.name == 'MNT':
        if offer.currency_needed.name == 'RUB':
            required_amount = offer.amount_offered / Decimal(mnt_to_rub)
        elif offer.currency_needed.name == 'USD':
            required_amount = offer.amount_offered / Decimal(mnt_to_usd)
    elif offer.currency_offered.name == 'USD':
        if offer.currency_needed.name == 'RUB':
            required_amount = offer.amount_offered * Decimal(rub_to_usd)
        elif offer.currency_needed.name == 'MNT':
            required_amount = offer.amount_offered * Decimal(mnt_to_usd)

    if required_amount is None:
        logger.error(f"Ошибка при расчете требуемой "
                     f"суммы для предложения: {offer}")
    else:
        logger.info(f"Расчетная требуемая сумма: {required_amount}")
    return {
        'rub_to_usd': rub_to_usd,
        'mnt_to_rub': mnt_to_rub,
        'mnt_to_usd': mnt_to_usd,
        'required_amount': required_amount
    }
