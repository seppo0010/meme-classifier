from dotenv import load_dotenv
load_dotenv()
import os
from telegram.ext import Updater, MessageHandler, Filters
import requests
import numpy as np
import pandas as pd
import cv2
import pickle
from meme_classifier.compare_images import compare_images

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
    photo = update['message'].effective_attachment[0]
    r = requests.get(photo.get_file()['file_path'])
    nparr = np.frombuffer(r.content, np.uint8)
    img_np = cv2.imdecode(nparr, flags=1)
    data = get_row(img_np)
    df = pd.DataFrame([data], columns=columns)
    proba = classifier.predict_proba(df)[0]
    index = np.argmax(proba)
    val = np.argmax(proba)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{templates[index-1][1]} ({proba[index]})')

tag_handler = MessageHandler(Filters.photo & (~Filters.command), tag)

updater.dispatcher.add_handler(tag_handler)
updater.start_polling()
