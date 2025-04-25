from telegram import Bot


def post_to_telegram(token: str,
                     channel_id: str,
                     text: str,
                     image_url: str | None = None) -> None:
    bot = Bot(token=token)

    if image_url:
        bot.send_photo(chat_id=channel_id,
                       photo=image_url,
                       caption=text,
                       timeout=30)
    else:
        bot.send_message(chat_id=channel_id,
                         text=text,
                         timeout=30)

    print(f"Message posted to Telegram channel {channel_id}")
