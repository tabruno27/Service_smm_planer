import time
from datetime import datetime
from scr.sheets import authorize_google_sheets, fetch_text_from_google_doc
from scr.vk import post_to_vk
from scr.tg import post_to_telegram


def process_schedule(vk_token, telegram_token, vk_group_id, telegram_channel_id, sheet_name="SMM-planer"):
    client = authorize_google_sheets()
    sheet = client.open(sheet_name).sheet1
    records = sheet.get_all_records()

    for record in records:
        post_date = datetime.strptime(record['Дата'], '%H:%M %d.%m.%Y')
        now = datetime.now()

        if now >= post_date:
            try:
                message = fetch_text_from_google_doc(record['Ссылка на документ'])
            except Exception as e:
                print(f"Failed to fetch document: {e}")
                continue

            social_networks = [s.strip().lower() for s in record['Соцсеть'].split(',')]
            
            for network in social_networks:
                if network == 'вконтакте':
                    post_to_vk(vk_token, vk_group_id, message)
                elif network == 'телеграм':
                    post_to_telegram(telegram_token, telegram_channel_id, message)
        time.sleep(60)
