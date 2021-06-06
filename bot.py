from dotenv import load_dotenv
load_dotenv()

import os
import logging
import io
import re
import json

import psycopg2
from telegram import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, InlineQueryHandler, CallbackQueryHandler

from meme_classifier.images import process_image, templates

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

def make_buttons(record, srid, index):
    buttons = [
        [
            InlineKeyboardButton(text='<', callback_data=json.dumps({'action': 'update_res', 'index': index - 1, 'srid': srid})),
            InlineKeyboardButton(text='>', callback_data=json.dumps({'action': 'update_res', 'index': index + 1, 'srid': srid})),
        ],
    ]
    if record['template']:
        buttons.append([
            InlineKeyboardButton(
                text='Bad template',
                callback_data=json.dumps({'action': 'bad_template', 'id': record['id']})
            )
        ])
    return buttons

def send_search_result(chat_id, record, srid, index, context, num_records):
    template = ''
    if record['display_name'] is not None:
        template = f" ({record['display_name']})"
    context.bot.copy_message(
        chat_id=chat_id,
        from_chat_id=record['chat_id'],
        message_id=record['message_id'],
        caption=f"Result {index+1}/{num_records}{template}",
        reply_markup=InlineKeyboardMarkup(make_buttons(record, srid, index)),
    )

def search(update, context):
    cur = conn.cursor()
    cur.execute("DELETE FROM search_results WHERE date < NOW() - INTERVAL '1 DAY'")
    conn.commit()

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
          WHERE (tsv @@ q) OR LOWER(display_name) LIKE LOWER(%s)
        ) AS t1 ORDER BY ts_rank_cd(t1.tsv, plainto_tsquery(%s)) DESC LIMIT 50;
        ''', [criteria, f'%{criteria}%', criteria]
        )
    res = [dict(zip(('chat_id', 'message_id', 'template', 'display_name', 'id'), row)) for row in cur.fetchall()]
    if len(res) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'no results :(')
        return

    cur = conn.cursor()
    cur.execute("INSERT INTO search_results (results) VALUES (%s) RETURNING id", [json.dumps(res)])
    srid = cur.fetchone()[0]
    conn.commit()

    record = res[0]
    chat_id = update['message']['chat']['id']
    send_search_result(chat_id, record, srid, 0, context, len(res))

def bad_template_handler(update, context):
    id = json.loads(update['callback_query']['data'])['id']
    cur = conn.cursor()
    cur.execute("UPDATE meme SET bad_template = template, template = 0 WHERE id = %s", (id,))
    conn.commit()
    context.bot.edit_message_caption(update['callback_query']['message']['chat']['id'], message_id=update['callback_query']['message']['message_id'], caption=None, reply_markup=InlineKeyboardMarkup([]))


def update_result_handler(update, context):
    callback_data = json.loads(update['callback_query']['data'])
    srid = callback_data['srid']
    cur = conn.cursor()
    cur.execute(
    '''
    SELECT results FROM search_results WHERE id = %s
    ''', [srid])
    f = cur.fetchone()
    if f is None or len(f) == 0:
        return

    chat_id = update['callback_query']['message']['chat']['id']
    res = json.loads(f[0])
    index = callback_data['index']
    if index < 0 or index >= len(res):
        context.bot.send_message(chat_id=chat_id, text=f'no more results')
        return

    record = res[index]
    replay_markup = InlineKeyboardMarkup(make_buttons(record, srid, index))
    message_id = update['callback_query']['message']['message_id']
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=message_id,
    )
    send_search_result(chat_id, record, srid, index, context, len(res))

def callback_handler(update, context):
    {
        'bad_template': bad_template_handler,
        'update_res': update_result_handler,
    }[json.loads(update['callback_query']['data'])['action']](update, context)


updater.bot.set_my_commands([BotCommand('search', 'searches for a meme')])
updater.dispatcher.add_handler(MessageHandler(Filters.photo & (~Filters.command), tag))
updater.dispatcher.add_handler(CommandHandler('search', search))
updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler))
updater.start_polling()
