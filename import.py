from dotenv import load_dotenv
load_dotenv()

import sys
import os
import re
import json

import psycopg2

from meme_classifier.images import process_image

path = sys.argv[1]
data = json.load(open(os.path.join(path, 'result.json'), 'r'))
chat_id = data['id']
conn = psycopg2.connect(os.getenv('POSTGRES_CREDENTIALS'))

for m in data['messages']:
    if 'photo' in m:
        template, text = process_image(open(os.path.join(path, m['photo']), 'rb'))
        message_id = m['id']
        print(f'processing message {message_id}')

        cur = conn.cursor()
        cur.execute("INSERT INTO meme (template, text, chat_id, message_id) VALUES (%s, %s, %s, %s)", (template, text, chat_id, message_id))
        conn.commit()
