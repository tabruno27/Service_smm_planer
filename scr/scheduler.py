from datetime import datetime, timezone
from typing import List

from scr.sheets import authorize_google_sheets, fetch_text_from_google_doc, load_targets
from scr.vk import post_to_vk
from scr.tg import post_to_telegram
from scr.ok import post_to_ok
from scr.constants import (STATUS_COL, DATE_COL, TIME_COL, DOC_COL,
                           SOCIAL_COL, IMAGE_COL, STATUS_COL_EXTRA)
from scr.utils.google import extract_doc_id
from scr.constants import LOCAL_TZ
from scr.constants import OK_MARK, FAIL_MARK



def scan_sheet(
    vk_token: str,
    telegram_token: str,
    vk_group_id: int,
    telegram_channel_id: str,
    ok_app_key: str,
    ok_access_token: str,
    sheet_name: str = "SMM-planer",
) -> None:
    """Читает Google-Sheet и публикует записи, время в таблице хранится в UTC."""
    ws = authorize_google_sheets().open(sheet_name).sheet1
    targets = load_targets()
    header = ws.row_values(1)
    status_col = header.index(STATUS_COL) + 1
    try:
        status_col_extra = header.index(STATUS_COL_EXTRA) + 1
    except ValueError:
        status_col_extra = None
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
        vk_targets = targets.get("вконтакте", [])
        has_extra_groups = len(vk_targets) >= 2
        target_tg = targets.get("телеграм", [telegram_channel_id])
        ok_groups = targets.get("одноклассники", [])

        # ---------- ОТПРАВКА ----------
        posted = False
        posted_extra = False
        need_extra_status = False  # Флаг, нужен ли статус для доп. группы
        try:
            if net == "вконтакте":
                if len(vk_targets) > 0:
                    main_group = vk_targets[0]
                    post_to_vk(main_group["token"], main_group["id"], message, image_url)
                    posted = True
                
                if has_extra_groups:
                    for extra_group in vk_targets[1:]:
                        post_to_vk(extra_group["token"], extra_group["id"], message, image_url)
                        posted_extra = True
                    need_extra_status = True
            elif net == "телеграм":
                for tg_chan in targets.get("телеграм", target_tg):
                    post_to_telegram(telegram_token, tg_chan, message, image_url)
                    posted = True
            elif net == "одноклассники":
                for ok_group_id in ok_groups:
                    post_to_ok(
                        app_key=ok_app_key,
                        access_token=ok_access_token,
                        group_id=ok_group_id,
                        message=message,
                        image_url=image_url
                    )
                    posted = True
        except Exception as e:
            print(f"[row {idx}] Ошибка постинга: {e}")

        ws.update_cell(idx, status_col, OK_MARK if posted else FAIL_MARK)
        if status_col_extra and need_extra_status:
            ws.update_cell(idx, status_col_extra, OK_MARK if posted_extra else FAIL_MARK)
        elif status_col_extra:
            # Очищаем статус для не-ВК соцсетей
            ws.update_cell(idx, status_col_extra, "")
        print(f"[row {idx}] {'Опубликовано' if posted else 'Не отправлено'} в {net}!")