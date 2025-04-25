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

    header = ws.row_values(1)                    # ['телеграм', 'одноклассники', 'вконтакте']
    columns = ws.get_all_values()[1:]            # всё после первой строки

    targets: dict[str, list] = {h.strip().lower(): [] for h in header}

    for row in columns:
        for col_idx, cell in enumerate(row, start=0):
            name = header[col_idx].strip().lower()
            inner_target_link = cell.strip()
            if inner_target_link:
                if name == "вконтакте":
                    try:
                        inner_target_link = int(inner_target_link)
                    except ValueError:
                        continue
                targets[name].append(inner_target_link)

    return targets