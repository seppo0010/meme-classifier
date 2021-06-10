import os
import io

from telethon import TelegramClient
import tweepy

tg = TelegramClient(
    'anon',
    api_id=os.getenv('TELEGRAM_API_ID'),
    api_hash=os.getenv('TELEGRAM_API_HASH'),
)

auth = tweepy.OAuthHandler(os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET'))
auth.set_access_token(os.getenv('TWITTER_ACCESS_TOKEN'), os.getenv('TWITTER_SECRET_TOKEN'))
tweepy_api = tweepy.API(auth)

async def main():
    message = await tg.get_messages(-1001408931466, ids=16698)
    media_data = io.BytesIO()
    await tg.download_media(message, file=media_data, thumb=-1)
    media_data.seek(0)

    media = tweepy_api.media_upload('', file=media_data)
    tweepy_api.update_status('', media_ids=[media.media_id_string])



tg.start(os.getenv('TELEGRAM_PHONE'))
with tg:
    tg.loop.run_until_complete(main())
