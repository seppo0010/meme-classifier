from dotenv import load_dotenv
load_dotenv()

import os
import logging
import io

import psycopg2
from telegram import BotCommand
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

from meme_classifier.images import process_image

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

conn = psycopg2.connect(os.getenv('POSTGRES_CREDENTIALS'))
updater = Updater(token=os.getenv('TELEGRAM_TOKEN'), use_context=True)

def tag(update, context):
    logger.info('tagging a message')
    if update['message'] is not None:
        photo = update['message'].effective_attachment[-1]
        chat_id = update['message']['chat']['id']
        message_id = update['message']['message_id']
    else:
        photo = update['channel_post']['photo'][-1]
        chat_id = update['channel_post']['sender_chat']['id']
        message_id = update['channel_post']['message_id']
    b = io.BytesIO()
    content = photo.get_file().download(out=b)
    content.seek(0)
    template, text = process_image(content)

    cur = conn.cursor()
    cur.execute("INSERT INTO meme (template, text, chat_id, message_id) VALUES (%s, %s, %s, %s)", (template, text, chat_id, message_id))
    conn.commit()

    # context.bot.forward_message(chat_id=update['message']['chat']['id'], from_chat_id=update['message']['chat']['id'], message_id=update['message']['message_id'])
    # context.bot.send_message(chat_id=update.effective_chat.id, text=f'{templates[index-1][1]} ({proba[index]})\ntext: {text}')

def search(update, context):
    texts = update['message']['text'].split(' ', 2)
    if len(texts) == 1:
        return
    criteria = texts[1]
    cur = conn.cursor()
    cur.execute(
    '''
    SELECT chat_id, message_id FROM (
      SELECT chat_id, message_id, tsv
      FROM meme, plainto_tsquery(%s) AS q
      WHERE (tsv @@ q)
    ) AS t1 ORDER BY ts_rank_cd(t1.tsv, plainto_tsquery(%s)) DESC LIMIT 5;
    ''', [criteria, criteria]
    )
    found = False
    for record in cur:
        found = True
        context.bot.forward_message(chat_id=update['message']['chat']['id'], from_chat_id=record[0], message_id=record[1])

    if not found:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'no results :(')

updater.bot.set_my_commands([BotCommand('search', 'searches for a meme')])
updater.dispatcher.add_handler(MessageHandler(Filters.photo & (~Filters.command), tag))
updater.dispatcher.add_handler(CommandHandler('search', search))

updater.start_polling()
