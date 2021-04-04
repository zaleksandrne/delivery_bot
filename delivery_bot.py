import json, os, requests

from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Filters, MessageHandler, Updater)

load_dotenv()


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DELLIN_KEY = os.getenv('DELLIN_KEY')
DELLIN_ID = os.getenv('DELLIN_ID')
URL_DELLIN_CALC = os.getenv('URL_DELLIN_CALC')
URL_DELLIN_KLADR = os.getenv('URL_DELLIN_KLADR')

URL_SBER = os.getenv('URL_SBER')

URL_GLAVDOSTAVKA = os.getenv('URL_GLAVDOSTAVKA')

USERS = {}

bot = Bot(TELEGRAM_TOKEN)
updater = Updater(TELEGRAM_TOKEN)


def start(update, context):
    USERS[update.effective_user.id] = {
            'progress': 1,
            'derival': '',
            'arrival': ''
            }
    bot.send_message(update.effective_message.chat.id,
                     'Введите город отправления посылки'
                     )


def progress(update, context):
    if USERS[update.effective_user.id]['progress'] == 1:
        return city(update, context)
    elif USERS[update.effective_user.id]['progress'] == 2:
        return result(update, context)


def city(update: Update, context: CallbackContext):
    USERS[update.effective_user.id]['derival'] = update['message']['text']
    USERS[update.effective_user.id]['progress'] = 2
    bot.send_message(update.effective_message.chat.id,
                     'Введите город получения посылки'
                     )


def result(update: Update, context: CallbackContext):
    USERS[update.effective_user.id]['arrival'] = update['message']['text']
    derival = USERS[update.effective_user.id]['derival'].lower()
    arrival = USERS[update.effective_user.id]['arrival'].lower()
    derival_dellin = requests.post(
        URL_DELLIN_KLADR,
        json={"appkey": DELLIN_KEY,
              "q": derival,
              "limit": 1}
        )
    arrival_dellin = requests.post(
        URL_DELLIN_KLADR,
        json={"appkey": DELLIN_KEY,
              "q": arrival,
              "limit": 1}
        )
    try:
        derival_dellin = derival_dellin.json().get('cities')[0]['code']
        arrival_dellin = arrival_dellin.json().get('cities')[0]['code']
    except IndexError:
        del USERS[update.effective_user.id]
        keyboard = [[InlineKeyboardButton(
            'Новый расчет',
            callback_data='new'
            )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(update.effective_message.chat.id,
                         'Ошибка в названии города. Попробуйте еще.',
                         reply_markup=reply_markup
                         )

    dellin = requests.post(
        URL_DELLIN_CALC,
        json={"appkey": DELLIN_KEY,
              "sessionID": DELLIN_ID,
              "derival": {"city": derival_dellin},
              "arrival": {"city": arrival_dellin}
              }
    )
    with open('sber_cities.json', 'r', encoding='utf-8') as g:
        sber_cities = json.load(g)
    derival_sber = [city['kladr_id'] for city in sber_cities \
                    if city.get('name').lower() == derival][0]
    arrival_sber = [city['kladr_id'] for city in sber_cities \
                    if city.get('name').lower() == arrival][0]
    sber = requests.post(
        URL_SBER,
        json={"id": "JsonRpcClient.js",
              "jsonrpc": "2.0",
              "method": "calculateShipping",
              "params": {
                  "stock": True,
                  "kladr_id_from": derival_sber,
                  "kladr_id": arrival_sber,
                  "length": 50,
                  "width": 35,
                  "height": 35,
                  "weight": 5,
                  "cod": 0,
                  "declared_cost": 0,
                  "courier": "sberlogistics"
                  }
              }
    )
    sber = sber.json()['result']['methods'][0]
    with open('glav_cities.json', 'r', encoding='utf-8') as g:
        GLAV_CITIES = json.load(g)
    derival_glav = [city['id'] for city in GLAV_CITIES \
                    if city.get('name', '').lower() == derival][0]
    arrival_glav = [city['id'] for city in GLAV_CITIES \
                    if city.get('name', '').lower() == arrival][0]
    glavdostavka = requests.post(
        URL_GLAVDOSTAVKA + f'&depPoint={derival_glav}&arrPoint={arrival_glav}'
        )
    price_glavdostavka = glavdostavka.json()['price']
    dellin = dellin.json()['data']['terminals_standard']
    price_dellin = dellin['price']
    period_dellin = dellin['period_to']
    price_sber = sber['cost']['total']['sum']
    period_sber = sber['max_days']
    del USERS[update.effective_user.id]
    keyboard = [[InlineKeyboardButton('Новый расчет', callback_data='new')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    derival = derival[0].upper() + derival[1:]
    arrival = arrival[0].upper() + arrival[1:]

    bot.send_message(update.effective_message.chat.id,
                     f'Стоимость и сроки доставки посылки с габаритами '
                     f'не превышающими 0.5х0.35х0.35(м) и массой не более 5кг '
                     f'из города {derival} в город {arrival} '
                     f'(от терминала до терминала):\n\n'
                     f'Деловые линии: {price_dellin} руб. '
                     f'До {period_dellin} дней.\n'
                     f'СберЛогистика: {price_sber} руб. '
                     f'До {period_sber} дней.\n'
                     f'ГлавДоставка: {price_glavdostavka} руб',
                     reply_markup=reply_markup
                     )


def button(update: Update, context: CallbackContext):
    start(update, context)


def main():
    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, progress))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
