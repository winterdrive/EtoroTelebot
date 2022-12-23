#!/usr/lib/python3.7
# -*- coding:UTF-8 -*-

import psutil
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater  # pip install python-telegram-bot

TOKEN = "5495772446:AAGcdNXEy5BbBo-QGxLcALw2HV-__mrcqlo"
CHAT_ID = "-1001423405758"


# 取得CARD_ID的JSON時，不能開自己在python裡運行的bot，要關掉用官方的
# http://blog.3dgowl.com/telegram-telegram%e4%ba%94-%e5%8f%96%e5%be%97-chat-id/

def start(bot, update):  # 新增指令/start
    message = update.message
    chat = message['chat']
    update.message.reply_text(text='Hello  ' + str(chat['first_name']))


def batteryAlert(bot, update):  # 新增指令/batteryAlert
    message = update.message

    def convertTime(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%d:%02d:%02d" % (hours, minutes, seconds)

    battery = psutil.sensors_battery()
    text = "Battery percentage : " + str(battery.percent) + "\n" + "Power plugged in : " + str(
        battery.power_plugged) + "\n" + "Battery left : " + str(convertTime(battery.secsleft))
    chat = message['chat']
    update.message.reply_text(text='Hello  ' + str(chat['first_name']) + "\n" + str(text))


def echo(bot, update):  # 新增指令/start
    message = update.message
    text = message.text + '<<<我沒有這個指令'
    update.message.reply_text(text=text)


# def send_message(event, context):
#     bot = telegram.Bot(token=TOKEN)
#     bot.sendMessage(chat_id = CHAT_ID, text = "Hey there!")

def main():
    # 創建一個Updater，並填入所申請之API TOKEN
    updater = Updater(TOKEN, use_context=False)
    # 定義一個dispatcher(調度器)
    dispatcher = updater.dispatcher
    # 使用CommandHandler定義Handler，並讓dispatcher註冊 handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('batteryAlert', batteryAlert))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    dispatcher.bot.send_message(chat_id=CHAT_ID, text='機器人啟動')

    # 啟始Bot
    updater.start_polling()
    # 按Ctrl + C 進行終止Bot 
    updater.idle()


if __name__ == '__main__':
    main()

# & c:/python/.venv/Scripts/python.exe c:/python/webscrapper/telegramBot.py
