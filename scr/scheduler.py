from datetime import datetime, timezone
from typing import List

from scr.sheets import authorize_google_sheets, fetch_text_from_google_doc, load_targets
from scr.vk import post_to_vk
from scr.tg import post_to_telegram
from scr.constants import (STATUS_COL, DATE_COL, TIME_COL, DOC_COL,
                           SOCIAL_COL, IMAGE_COL, EXTRA_PAGES_COL)
from scr.utils.google import extract_doc_id
from scr.constants import LOCAL_TZ
from scr.constants import OK_MARK, FAIL_MARK



def scan_sheet(
    vk_token: str,
    telegram_token: str,
    vk_group_id: int,
    telegram_channel_id: str,
    sheet_name: str = "SMM-planer",
) -> None:
    """Читает Google-Sheet и публикует записи, время в таблице хранится в UTC."""
    ws = authorize_google_sheets().open(sheet_name).sheet1
    targets = load_targets()
    header = ws.row_values(1)
    status_col = header.index(STATUS_COL) + 1
    records = ws.get_all_records()
    now_utc = datetime.now(timezone.utc)

    for idx, rec in enumerate(records, start=2):

        # ---------- ДАТА + ВРЕМЯ ----------
        date_raw = rec[DATE_COL].strip()
        time_raw = rec[TIME_COL].strip()

        if not date_raw or not time_raw:
            print(f"[row {idx}] Дата или время пустые — пропускаю")
            continue

        dt_str = f"{date_raw} {time_raw}"

        post_dt = None
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
            try:
                naive = datetime.strptime(dt_str, fmt)
                post_dt = LOCAL_TZ.localize(naive)
                post_dt = post_dt.astimezone(timezone.utc)
                break
            except ValueError:
                post_dt = None

        if post_dt is None:
            print(f"[row {idx}] Неверный формат даты/времени: {dt_str!r}")
            continue

        current_status = rec.get(STATUS_COL, "").strip().lower()
        if post_dt > now_utc or current_status == OK_MARK:
            continue

        # ---------- ТЕКСТ ----------
        doc_id = extract_doc_id(rec[DOC_COL])
        if not doc_id:
            print(f"[row {idx}] Нет ID документа — пропускаю")
            continue

        message = fetch_text_from_google_doc(doc_id).strip()
        if not message:
            print(f"[row {idx}] Пустой текст — пропускаю")
            continue

        # ---------- МЕДИА ----------
        image_url = rec.get(IMAGE_COL) or None

        # ---------- КУДА ПУБЛИКУЕМ ----------
        net = rec[SOCIAL_COL].strip().lower()     # теперь всегда одна соцсеть
        extra_vk = [int(p.strip()) for p in rec.get(EXTRA_PAGES_COL, "").split(",") if p.strip()]
        target_vk_pages = targets.get("вконтакте", []) + extra_vk
        target_tg = targets.get("телеграм", [telegram_channel_id])

        # ---------- ОТПРАВКА ----------
        posted = False
        try:
            if net == "вконтакте":
                for page in target_vk_pages:
                    post_to_vk(vk_token, page, message, image_url)
                    posted = True
            elif net == "телеграм":
                for tg_chan in targets.get("телеграм", target_tg):
                    post_to_telegram(telegram_token, tg_chan, message, image_url)
                    posted = True
            elif net == "одноклассники":
                for ok_page in targets.get("одноклассники", []):
                    print(f"[stub] OK posting to {ok_page} не реализован")
        except Exception as e:
            print(f"[row {idx}] Ошибка постинга: {e}")

        ws.update_cell(idx, status_col, OK_MARK if posted else FAIL_MARK)
        print(f"[row {idx}] {'Опубликовано' if posted else 'Не отправлено'}!")