import time
from telegram import Bot


def post_to_telegram(telegram_token, channel_id, message):
    bot = Bot(token=telegram_token)
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
