import os
import io
import urllib

from telethon import TelegramClient
import tweepy
import psycopg2

def getsecret(key):
    with open('/run/secrets/' + key.lower(), 'r') as fp:
        return fp.read().strip()

tg = TelegramClient(
    'anon',
    api_id=getsecret('TELEGRAM_API_ID'),
    api_hash=getsecret('TELEGRAM_API_HASH'),
)

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
    SELECT chat_id, message_id FROM meme WHERE date > %s AND upvotes >= 5 ORDER BY upvotes - downvotes DESC
    ''', [date])
    res = cur.fetchone()
    if res is None:
        return
    chat_id, message_id = res
    message = await tg.get_messages(chat_id, ids=message_id)
    media_data = io.BytesIO()
    await tg.download_media(message, file=media_data, thumb=-1)
    media_data.seek(0)

    media = tweepy_api.media_upload('', file=media_data)
    tweepy_api.update_status('', media_ids=[media.media_id_string])



tg.start(getsecret('TELEGRAM_PHONE'))
with tg:
    tg.loop.run_until_complete(main())
