import random, os, json, time
from telegram import Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Updater, CallbackContext,
                          CallbackQueryHandler, CommandHandler, MessageHandler, Filters)
from dotenv import load_dotenv

import json
import requests


load_dotenv()




TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DELLIN_KEY = os.getenv('DELLIN_KEY')
DELLIN_ID = os.getenv('DELLIN_ID')
URL_DELLIN_CALC = os.getenv('URL_DELLIN_CALC')
URL_DELLIN_KLADR = os.getenv('URL_DELLIN_KLADR')

URL_SBER = os.getenv('URL_SBER')

URL_GLAVDOSTAVKA = os.getenv('URL_GLAVDOSTAVKA')



QUESTION_MEMORY = {}
USERS = {}
TIMER_COUNT = 0

bot = Bot(TELEGRAM_TOKEN)
updater = Updater(TELEGRAM_TOKEN)


def start(update, context):
    if update.effective_user.id not in USERS:
        USERS[update.effective_user.id] = {
            'progress': 0,
            'derival': '',
            'arrival': ''
            }
        one(update, context)
    elif USERS[update.effective_user.id]['progress'] == 1:
        two(update, context)
    elif USERS[update.effective_user.id]['progress'] == 2:
        three(update, context)

   
              
    #USERS[update.effective_user.id] = 1

            
def one(update: Update, context: CallbackContext):
    update.message.reply_text('Введите город отправления')
    USERS[update.effective_user.id]['progress'] = 1

def two(update: Update, context: CallbackContext):
    USERS[update.effective_user.id]['derival'] = update['message']['text']
    USERS[update.effective_user.id]['progress'] = 2
    update.message.reply_text(f'Введите город получателя')


def three(update: Update, context: CallbackContext):
    USERS[update.effective_user.id]['arrival'] = update['message']['text']
    derival = USERS[update.effective_user.id]['derival'].lower()
    arrival = USERS[update.effective_user.id]['arrival'].lower()
    print(derival)
    print(arrival)
    
    derival_dellin = requests.post(
        URL_DELLIN_KLADR,
        json={"appkey": DELLIN_KEY,
              "q": derival,
              "limit":1}
        )
    derival_dellin = derival_dellin.json()['cities'][0]['code']
    arrival_dellin = requests.post(
        URL_DELLIN_KLADR,
        json={"appkey": DELLIN_KEY,
              "q": arrival,
              "limit":1}
        )
    arrival_dellin = arrival_dellin.json()['cities'][0]['code']
    dellin = requests.post(
        URL_DELLIN_CALC,
        json={"appkey": DELLIN_KEY,
              "sessionID": DELLIN_ID,
              "derival":{"city":derival_dellin},
              "arrival":{"city":arrival_dellin}
              }
    )
    sber = requests.post(
        URL_SBER,
        json={"id": "JsonRpcClient.js",
              "jsonrpc": "2.0",
              "method": "calculateShipping",
              "params": {
                  "stock": 'true',
                  "kladr_id_from": "77000000000",
                  "kladr_id": "36000001000",
                  "length": 50,
                  "width": 35,
                  "height": 35,
                  "weight": 5,
                  "cod": 0,
                  "declared_cost": 0,
                  "courier": "shiptor"
                  }
              }
    )

    with open('glav_cities.json', 'r', encoding='utf-8') as g:
        GLAV_CITIES = json.load(g)
    derival_glav = [city['id'] for city in GLAV_CITIES if city.get('name', '').lower() == derival.lower()][0]
    arrival_glav = [city['id'] for city in GLAV_CITIES if city.get('name', '').lower() == arrival.lower()][0]
    print(derival_glav)
    glavdostavka = requests.post(
        URL_GLAVDOSTAVKA + f'&depPoint={derival_glav}&arrPoint={arrival_glav}'
        )
    glavdostavka = glavdostavka.json()['price']
    print(glavdostavka)

    

    dellin = dellin.json()['data']['terminals_standard']
    price = dellin['price']
    period = dellin['period_to']
    update.message.reply_text(f'Среняя стоимость и сроки доставки от терминала до терминала')
    update.message.reply_text(f'Деловые линии: {price} руб. до {period} дней.')
    update.message.reply_text(f'ГлавДоставка: {glavdostavka} руб')

    USERS[update.effective_user.id]['progress'] = 0


start_handler = CommandHandler('start', start)
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(MessageHandler(Filters.text, start))
updater.start_polling()
updater.idle()
