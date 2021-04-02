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
URL_DELLIN_KLADR = os.getenv('URL_DELLIN_KLADR')

QUESTION_MEMORY = {}
PROGRESS = {}
TIMER_COUNT = 0

bot = Bot(TELEGRAM_TOKEN)
updater = Updater(TELEGRAM_TOKEN)


def start(update, context):
    if update.effective_user.id not in PROGRESS:
        PROGRESS[update.effective_user.id] = 0
        one(update, context)
    elif PROGRESS[update.effective_user.id] == 1:
        two(update, context)
    elif PROGRESS[update.effective_user.id] == 2:
        three(update, context)
   
              
    #PROGRESS[update.effective_user.id] = 1

            


def one(update: Update, context: CallbackContext):
    update.message.reply_text('Введите город отправления')
    derival = requests.post(
        URL_DELLIN_KLADR,
        json={"appkey": DELLIN_KEY,
            "q":"Мос",
            "limit":1}
        )


    print(derival.json()['cities'][0]['code'])
    PROGRESS[update.effective_user.id] = 1


def two(update: Update, context: CallbackContext):
    update.message.reply_text(f'Введите город отправления')
    arrival = requests.post(
        URL_DELLIN_KLADR,
        json={"appkey": DELLIN_KEY,
            "q":"Мос",
            "limit":1}
        )

    PROGRESS[update.effective_user.id] = 2


def three(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Введите город получателя')

    PROGRESS[update.effective_user.id] = 0


start_handler = CommandHandler('start', start)
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(MessageHandler(Filters.text, start))
updater.start_polling()
updater.idle()
