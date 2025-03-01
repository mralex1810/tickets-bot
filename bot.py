#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import traceback
import logging
from datetime import datetime
from threading import Thread
import time

import yaml
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ContextTypes

from models import Ticket, TicketSearch, Image, db
from peewee import fn
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

NUMBER_RE = re.compile(r'\d+')


def log(update: Update):
    if not update.message:
        return

    text = update.message.text
    chat = update.message.chat
    logger.info(f"{chat.username} {chat.first_name} {chat.last_name}: {text}")


def plain_match(field, query):
    pass

def scan(update, context):
    log(update)
    if update.message.chat.id != Config.ADMIN_ID:
        return

    bot = context.bot
    bot.send_chat_action(update.message.chat.id, "typing")

    try:
        db.drop_tables([Ticket, TicketSearch, Image])
        db.create_tables([Ticket, TicketSearch, Image])

        for dir in os.listdir(Config.PATH):
            if not os.path.isdir(os.path.join(Config.PATH, dir)) or dir.startswith("."):
                continue

            config = yaml.safe_load(open(os.path.join(Config.PATH, dir, "config.yml")).read())
            ticket = Ticket.create(id=dir, name=config["name"], tag=config["tag"])
            TicketSearch.create(rowid=int(dir), name=config["name"])

            for file in sorted(os.listdir(os.path.join(Config.PATH, dir))):
                if file.endswith(".yml"):
                    continue
                image = Image.create(
                    ticket=ticket,
                    filename=file
                )
    except Exception as e:
        update.message.reply_text("\u274c **Failed**:\n```" + traceback.format_exc() + "```", parse_mode="Markdown")
        return

    update.message.reply_text("\u2705 **Success**: update tickets", parse_mode="Markdown")


def start(update, context):
    log(update)
    update.message.reply_text(Config.WELCOME_MESSAGE, parse_mode="Markdown", disable_web_page_preview=True)


def help(update, context):
    log(update)
    update.message.reply_text(Config.HELP_MESSAGE, parse_mode="Markdown", disable_web_page_preview=True)

def send_tickets(update, tickets):
    response = ""
    for tid, name in tickets:
        response += "/{} {}\n".format(tid, name)
        if len(response) > 3900:
            update.message.reply_text(response)
            time.sleep(0.3)
            response = ""
    if response:
        update.message.reply_text(response)



def ticket(update: Update, context: ContextTypes.bot_data):
    if not update.message:
        return
    bot = context.bot
    text = update.message.text
    log(update)
    result = re.search(NUMBER_RE, text)
    if result is None:
        return search(update, context)

    num = int(result.group(0))
    try:
        ticket = Ticket.get(Ticket.id == num)
    except Ticket.DoesNotExist:
        update.message.reply_text("Не могу найти билет #{}\n\n/help — справка".format(num))
        return
    update.message.reply_text(ticket.name)

    for photo in ticket.image_set.order_by(Image.filename):
        if photo.file_id:
            bot.send_photo(update.message.chat.id, photo.file_id)
        else:
            if ".mp4" == photo.filename[-4:]:
                bot.send_chat_action(update.message.chat.id, "upload_video")
                with open(os.path.join(Config.PATH, str(num), photo.filename), "rb") as f:
                    message = bot.send_video(update.message.chat.id, f, supports_streaming=True)
            else:
                bot.send_chat_action(update.message.chat.id, "upload_photo")
                with open(os.path.join(Config.PATH, str(num), photo.filename), "rb") as f:
                    message = bot.send_photo(update.message.chat.id, f)
            photo.file_id = message.photo[-1].file_id
            photo.save()


def search(update: Update, context):
    response = ""
    cur = db.execute_sql('select rowid, name from ticketsearch(?)', (update.message.text,))
    tickets = [(rowid, name) for rowid, name in cur.fetchall()]
    if not tickets:
        update.message.reply_text("Ничего не найдено")
    else:
        send_tickets(update, tickets)


def dump_thread(update, context):
    bot = context.bot
    bot.send_chat_action(update.message.chat.id, "upload_photo")
    time.sleep(1)
    try:
        for photo in Image.select():
            time.sleep(1)
            if photo.file_id:
                bot.send_photo(update.message.chat.id, photo.file_id)
            else:
                bot.send_chat_action(update.message.chat.id, "upload_photo")
                with open(os.path.join(Config.PATH, str(photo.ticket.id), photo.filename), "rb") as f:
                    message = bot.send_photo(update.message.chat.id, f)
                photo.file_id = message.photo[-1].file_id
                photo.save()
    except:
        update.message.reply_text("\u274c **Failed**:\n```" + traceback.format_exc() + "```", parse_mode="Markdown")


def dump(update, context):
    log(update)
    if update.message.chat.id != Config.ADMIN_ID:
        update.message.reply_text("Данная функция недоступна для вашего аккаунта")
        return
    thread = Thread(target=dump_thread, args=(update, context))
    thread.start()

def error(update, context):
    logger.warning(str(context.error))

def tag_handler(update, context):
    if not update.message.text.startswith("/tag"):
        update.message.reply_text("Увы, я не могу понять о чем вы (а вы не можете понять о чем я)")
        return
    text = update.message.text[4:].strip()
    if not text:
        tags = Ticket.select(Ticket.tag.distinct())
        tags = ", ".join(tag.tag for tag in tags)
        if not tags:
            tags = "не знаю"
        update.message.reply_text("Теги, которые я знаю: " + tags)
        return
    response = ""
    tickets = Ticket.select(Ticket.id, Ticket.name).where(Ticket.tag == text)
    tickets = [(ticket.id, ticket.name) for ticket in tickets]
    if tickets:
        send_tickets(update, tickets)
    else:
        update.message.reply_text("Ничего не найдено по тегу " + text)


if __name__ == "__main__":
    updater = Updater(Config.TOKEN, request_kwargs={'read_timeout': 1000, 'connect_timeout': 1000}, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("scan", scan))
    dp.add_handler(CommandHandler("dump_all", dump))
    dp.add_handler(CommandHandler("tag", tag_handler))
    dp.add_handler(MessageHandler(Filters.all, ticket))
    dp.add_error_handler(error)

    logger.info("Starting...")
    db.connect()
    db.create_tables([Ticket, TicketSearch, Image])

    logger.info("Dropping old webhook...")
    updater.bot.delete_webhook()

    if Config.WEBHOOK:
        logger.info("Start webhook...")
        updater.start_webhook(listen='0.0.0.0', url_path='/', webhook_url=Config.WEBHOOK)
    else:
        logger.info("Start polling...")
        updater.start_polling()

    updater.idle()
