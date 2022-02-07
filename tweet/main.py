import os
import io
import urllib
from tempfile import NamedTemporaryFile

from imgurpython import ImgurClient
from telethon import TelegramClient
import tweepy
import psycopg2
import requests

def getsecret(key):
    with open('/run/secrets/' + key.lower(), 'r') as fp:
        return fp.read().strip()

tg = TelegramClient(
    'anon',
    api_id=getsecret('TELEGRAM_API_ID'),
    api_hash=getsecret('TELEGRAM_API_HASH'),
)

imgur = ImgurClient(getsecret('IMGUR_CLIENT_ID'), getsecret('IMGUR_CLIENT_SECRET'), getsecret('IMGUR_ACCESS_TOKEN'), getsecret('IMGUR_REFRESH_TOKEN'))
instagram_user_id, instagram_access_token = getsecret('INSTAGRAM_USER_ID'), getsecret('INSTAGRAM_ACCESS_TOKEN')
auth = tweepy.OAuthHandler(getsecret('TWITTER_API_KEY'), getsecret('TWITTER_API_SECRET'))
auth.set_access_token(getsecret('TWITTER_ACCESS_TOKEN'), getsecret('TWITTER_SECRET_TOKEN'))
tweepy_api = tweepy.API(auth)
pg_user = os.getenv("POSTGRES_USER")
pg_host = 'database'
pg_db = os.getenv("POSTGRES_DB")
with open('/run/secrets/postgres-password', 'r') as fp:
    pg_password = fp.read().strip()
dsn = f'postgres://{pg_user}:{urllib.parse.quote(pg_password)}@{pg_host}/{pg_db}'
conn = psycopg2.connect(dsn)

async def main():
    date = tweepy_api.home_timeline(1)[0].created_at
    cur = conn.cursor()
    cur.execute(
    '''
    SELECT chat_id, message_id FROM meme WHERE date > %s AND upvotes >= 4 ORDER BY upvotes - downvotes DESC
    ''', [date])
    res = cur.fetchone()
    if res is None:
        return
    chat_id, message_id = res
    message = await tg.get_messages(chat_id, ids=message_id)
    media_data = io.BytesIO()
    await tg.download_media(message, file=media_data, thumb=-1)
    media_data.seek(0)

    with NamedTemporaryFile() as image:
        image.write(media_data.read())
        image.flush()
        imgur_path = imgur.upload_from_path(image.name, anon=False)['link']
    media_data.seek(0)

    try:
        r = requests.post(
            f'https://graph.facebook.com/v11.0/{instagram_user_id}/media?image_url={imgur_path}&access_token={instagram_access_token}'
        ).json()
        creation_id = r['id']
        r = requests.post(
            f'https://graph.facebook.com/v11.0/{instagram_user_id}/media_publish?creation_id={creation_id}&access_token={instagram_access_token}'
        ).json()
    except:
        print('failed', r)
        pass

    media = tweepy_api.media_upload('', file=media_data)
    tweepy_api.update_status('', media_ids=[media.media_id_string])


tg.start(getsecret('TELEGRAM_PHONE'))
with tg:
    tg.loop.run_until_complete(main())
