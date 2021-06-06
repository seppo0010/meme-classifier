from dotenv import load_dotenv
load_dotenv()

import os
import pickle
try:
    from PIL import Image
except ImportError:
    import Image
import logging
import io

import numpy as np
import pandas as pd
import pytesseract
import cv2
from matplotlib import cm
import psycopg2
from telegram import BotCommand
from telegram.ext import Updater, MessageHandler, Filters

from meme_classifier.compare_images import compare_images

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

conn = psycopg2.connect(os.getenv('POSTGRES_CREDENTIALS'))

updater = Updater(token=os.getenv('TELEGRAM_TOKEN'), use_context=True)
template_path = 'template'
templates = [(1+i, f, cv2.imread(os.path.join(template_path, f))) for i, f in enumerate(os.listdir(template_path)) if os.path.isfile(os.path.join(template_path, f))]
csv_path = 'train_data.csv'
classifier = pickle.load(open(f'notebooks/classifier-{csv_path}.pickle', "rb"))

columns = []
for t in templates:
    columns.append(t[1] + '_similarity')
    columns.append(t[1] + '_mse')
    columns.append(t[1] + '_compare_hist')

def get_row(after):
    cols = []
    for _, template_name, template_image in templates:
        comparison = compare_images(template_image, after)
        cols.extend((comparison['similarity'], comparison['mse'], comparison['compare_hist']))
    return cols

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
    nparr = np.frombuffer(content.read(), np.uint8)

    img_np = cv2.imdecode(nparr, flags=1)
    # cv2.imwrite('cv.jpg', img_np)

    data = get_row(img_np)
    df = pd.DataFrame([data], columns=columns)
    proba = classifier.predict_proba(df)[0]
    index = np.argmax(proba)
    val = np.argmax(proba)

    content.seek(0)
    pil_image = Image.open(content)
    # pil_image.save("pil.jpg", "JPEG")

    text = '\n'.join((
        pytesseract.image_to_string(pil_image, lang='eng'),
        pytesseract.image_to_string(pil_image, lang='spa'),
    ))

    cur = conn.cursor()
    cur.execute("INSERT INTO meme (template, text, chat_id, message_id) VALUES (%s, %s, %s, %s)", (int(index), text, chat_id, message_id))
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
    for record in cur:
        context.bot.forward_message(chat_id=update['message']['chat']['id'], from_chat_id=record[0], message_id=record[1])

updater.bot.set_my_commands([BotCommand('search', 'searches for a meme')])
updater.dispatcher.add_handler(MessageHandler(Filters.photo & (~Filters.command), tag))
updater.dispatcher.add_handler(MessageHandler(Filters.command, search))
updater.start_polling()
