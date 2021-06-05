import sys
import os
import re
from bs4 import BeautifulSoup

path = sys.argv[1]
chat_id = int(sys.argv[2])

def process_file(filepath):
    with open(filepath, 'r') as fp:
        soup = BeautifulSoup(fp, 'html.parser')
    for link in soup.find_all('a', {'class': 'photo_wrap clearfix pull_left'}):
        message_id = re.search(r'_([0-9]+)@', link['href']).groups(1)[0]
        template, text = process_image(link['href'])
        save_image(chat_id, message_id, template, text)

for filename in os.listdir(path):
    filepath = os.path.join(path, filename)
    if os.path.isfile(filepath) and filepath.endswith('.html'):
        process_file(filepath)
