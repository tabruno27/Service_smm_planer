import time
from telegram import Bot


def post_to_telegram(token, channel_id, message, image_url=None):
    bot = Bot(token=token)

    if image_url:
        bot.send_photo(chat_id=channel_id, photo=image_url, caption=message, timeout=30)
    else:
        bot.send_message(chat_id=channel_id, text=message, timeout=30)

    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        try:
            bot.send_message(chat_id=channel_id, text=message, timeout=30)
            print(f"Message posted to Telegram channel {channel_id}")
            break
        except Exception as e:
            print(f"An error occurred while posting to Telegram (attempt {attempt + 1}): {str(e)}")
            attempt += 1
            time.sleep(5)
