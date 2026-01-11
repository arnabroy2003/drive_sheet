from googleapiclient.discovery import build
from google.oauth2 import service_account
import gspread

# ---- 1. Authenticate ----
SERVICE_ACCOUNT_FILE = 'creds.json'  # path to your service account JSON
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=credentials)
gc = gspread.authorize(credentials)

# ---- 2. Variables ----
FOLDER_ID = '1_9gcueWkHvg8zZiRGEOedUZUSuChtNpA'
SPREADSHEET_ID = '1B1fJ0olttKcqW_7wtc-YB5bWrj1Xrpv2_eReCYWQCqo'
SHEET_NAME = 'Sheet1'

pdf_links = []

# ---- 3. Paginated listing ----
page_token = None
while True:
    response = drive_service.files().list(
        q=f"'{FOLDER_ID}' in parents and trashed=false",
        fields="nextPageToken, files(id, name)",
        pageSize=100,   # max per API request
        pageToken=page_token
    ).execute()

    for f in response.get('files', []):
        file_id = f['id']
        file_name = f['name']

        # Make file shareable
        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        # Create shareable link
        share_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        pdf_links.append([file_name, share_link])

    page_token = response.get('nextPageToken')
    if not page_token:
        break  # no more pages

# ---- 4. Push to Google Sheet ----
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
sheet.append_rows(pdf_links, value_input_option="RAW")

print(f"✅ Done! Uploaded {len(pdf_links)} file names & links to sheet.")
