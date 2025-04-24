from datetime import datetime, timezone
from typing import List

from scr.sheets import authorize_google_sheets, fetch_text_from_google_doc
from scr.vk import post_to_vk
from scr.tg import post_to_telegram
from scr.constants import (
    STATUS_COL, DATE_COL, DOC_COL, SOCIAL_COL,
    IMAGE_COL, EXTRA_PAGES_COL
)
from scr.utils.google import extract_doc_id



def scan_sheet(
    vk_token: str,
    telegram_token: str,
    vk_group_id: int,
    telegram_channel_id: str,
    sheet_name: str = "SMM-planer",
) -> None:
    """Читает Google-Sheet и публикует просроченные записи (время в таблице задаётся в UTC)."""
    ws = authorize_google_sheets().open(sheet_name).sheet1

    # вычисляем номера колонок один раз
    header = ws.row_values(1)
    status_col = header.index(STATUS_COL) + 1      # gspread 1-based

    records = ws.get_all_records()
    now = datetime.now(timezone.utc)

    for idx, rec in enumerate(records, start=2):
        # 1) дата/время поста
        try:
            post_dt = datetime.strptime(rec[DATE_COL], "%H:%M %d.%m.%Y").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"[row {idx}] Неверный формат даты: {rec[DATE_COL]!r}")
            continue

        if post_dt > now or rec.get(STATUS_COL) == "✅":
            continue                    # ещё рано или уже опубликовано

        # 2) текст из Google Doc
        doc_id = extract_doc_id(rec[DOC_COL])
        if not doc_id:
            print(f"[row {idx}] Нет ID документа — пропускаю")
            continue

        message = fetch_text_from_google_doc(doc_id).strip()
        if not message:
            print(f"[row {idx}] Пустой текст — пропускаю")
            continue

        # 3) картинка (может отсутствовать)
        image_url = rec.get(IMAGE_COL) or None

        # 4) соцсети
        networks: List[str] = [s.strip().lower() for s in rec[SOCIAL_COL].split(",")]

        # 5) дополнительные группы VK
        extra_vk = [int(p.strip()) for p in rec.get(EXTRA_PAGES_COL, "").split(",") if p.strip()]
        target_vk_pages = [vk_group_id] + extra_vk

        # 6) публикация
        posted_ok = False
        for net in networks:
            try:
                if net == "вконтакте":
                    for page in target_vk_pages:
                        post_to_vk(vk_token, page, message, image_url)
                        posted_ok = True
                elif net == "телеграм":
                    post_to_telegram(telegram_token, telegram_channel_id, message, image_url)
                    posted_ok = True
            except Exception as e:
                print(f"[row {idx}] Ошибка постинга в {net}: {e}")

        # 7) отметка статуса
        new_status = "✅" if posted_ok else "error"
        ws.update_cell(idx, status_col, new_status)
        print(f"[row {idx}] {'Опубликовано' if posted_ok else 'Не отправлено'}!")