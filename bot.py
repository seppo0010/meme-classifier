from dotenv import load_dotenv
load_dotenv()

import os
import logging
import io
import re

import psycopg2
from telegram import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, InlineQueryHandler, CallbackQueryHandler

from meme_classifier.images import process_image, templates

print([t[1] for t in templates])

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
    template = re.match('^template=([0-9]+)$', criteria)
    cur = conn.cursor()
    if template:
        cur.execute(
        '''
        SELECT chat_id, message_id, template, display_name, meme.id FROM meme LEFT JOIN meme_template ON meme.template = meme_template.id WHERE template = %s
        ''', [template.group(1)])
    else:
        cur.execute(
        '''
        SELECT chat_id, message_id, template, display_name, id FROM (
          SELECT chat_id, message_id, template, display_name, meme.id, tsv
          FROM meme
          LEFT JOIN meme_template ON meme.template = meme_template.id, plainto_tsquery(%s) AS q
          WHERE (tsv @@ q)
        ) AS t1 ORDER BY ts_rank_cd(t1.tsv, plainto_tsquery(%s)) DESC LIMIT 5;
        ''', [criteria, criteria]
        )
    found = False
    for record in cur:
        found = True
        markup = None
        replay_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Bad template', callback_data=record[4])],
        ]) if record[2] else None
        context.bot.copy_message(
            chat_id=update['message']['chat']['id'],
            from_chat_id=record[0],
            message_id=record[1],
            caption=record[3],
            reply_markup=replay_markup,
        )

    if not found:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'no results :(')

def bad_template_handler(update, context):
    cur = conn.cursor()
    cur.execute("UPDATE meme SET bad_template = template, template = 0 WHERE id = %s", (update['callback_query']['data'],))
    conn.commit()
    context.bot.edit_message_caption(update['callback_query']['message']['chat']['id'], message_id=update['callback_query']['message']['message_id'], caption=None, reply_markup=InlineKeyboardMarkup([]))

updater.bot.set_my_commands([BotCommand('search', 'searches for a meme')])
updater.dispatcher.add_handler(MessageHandler(Filters.photo & (~Filters.command), tag))
updater.dispatcher.add_handler(CommandHandler('search', search))
updater.dispatcher.add_handler(CallbackQueryHandler(bad_template_handler))
# MessageHandler(Filters.text(['Bad template']), bad_template_handler)
updater.start_polling()
