import gspread
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials
from scr.utils.ficha import format_text


def authorize_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('t-osprey-457618-g6-3f1c8cc61184.json', scope)
    client = gspread.authorize(creds)
    return client


def fetch_text_from_google_doc(doc_id):
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    credentials = service_account.Credentials.from_service_account_file(
        't-osprey-457618-g6-3f1c8cc61184.json', scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)

    try:
        document = service.documents().get(documentId=doc_id).execute()
    except HttpError as e:
        print(f"Failed to fetch document: {e}")
        return ""

    doc_content = document.get('body').get('content')
    full_text = ''
    for value in doc_content:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text_run = elem.get('textRun')
                if text_run:
                    full_text += text_run.get('content')

    formatted_text = format_text(full_text)
    return formatted_text


def load_targets(book_name: str = "SMM-planer",
                 system_sheet: str = "links") -> dict[str, list]:
    client = authorize_google_sheets()
    ws = client.open(book_name).worksheet(system_sheet)

    header = [h.strip().lower() for h in ws.row_values(1)]
    data   = ws.get_all_values()[1:]                  # строки 2+

    # базовая структура
    targets: dict[str, list] = {
        "телеграм": [],
        "одноклассники": [],
        "вконтакте": []
    }

    # индексы нужных колонок
    try:
        col_tg   = header.index("телеграм")
    except ValueError:
        col_tg = None

    try:
        col_ok   = header.index("одноклассники")
    except ValueError:
        col_ok = None

    try:
        col_vk   = header.index("вконтакте")
        col_vk_t = header.index("vk_token")
    except ValueError:
        col_vk = col_vk_t = None

    for row in data:
        # -------- телеграм --------
        if col_tg is not None and len(row) > col_tg:
            chan = row[col_tg].strip()
            if chan:
                targets["телеграм"].append(chan)

        # -------- одноклассники --------
        if col_ok is not None and len(row) > col_ok:
            ok_link = row[col_ok].strip()
            if ok_link:
                targets["одноклассники"].append(ok_link)

        # -------- вконтакте + token --------
        if col_vk is not None and col_vk_t is not None \
           and len(row) > max(col_vk, col_vk_t):

            vk_id_raw   = row[col_vk].strip()
            vk_token    = row[col_vk_t].strip()

            if vk_id_raw and vk_token:
                try:
                    vk_id = int(vk_id_raw)
                except ValueError:
                    # если ID не число — пропускаем строку
                    continue
                targets["вконтакте"].append({"id": vk_id, "token": vk_token})

    return targets