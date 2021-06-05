from dotenv import load_dotenv
load_dotenv()
import os
from telegram.ext import Updater, MessageHandler, Filters
import numpy as np
import pandas as pd
import cv2
import pickle
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
import cv2
from matplotlib import cm
import io

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
    photo = update['message'].effective_attachment[-1]
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
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{templates[index-1][1]} ({proba[index]})\ntext: {text}')

tag_handler = MessageHandler(Filters.photo & (~Filters.command), tag)

updater.dispatcher.add_handler(tag_handler)
updater.start_polling()
