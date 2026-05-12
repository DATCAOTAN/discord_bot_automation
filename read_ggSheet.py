from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import os

# Đường dẫn tới tệp JSON chứa thông tin xác thực (tải từ Google Cloud Console).
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ID của Google Sheets (trích từ URL).
# Lấy từ phần sau "spreadsheets/d/" và trước "/edit"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Tên của sheet (tab) trong Google Sheets
SHEET_NAME = 'DISCORD 1-200'  # Đổi thành tên chính xác của sheet

# Xác thực
try:
    if not SERVICE_ACCOUNT_FILE or not SHEET_ID:
        raise ValueError("Missing Google Sheets config: GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SHEET_ID")
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    print("Xác thực thành công.")
except Exception as e:
    print("Lỗi khi xác thực:", e)
    exit()

# Đọc dữ liệu từ Google Sheet
try:
    sheet = service.spreadsheets()
    range_to_read = f'{SHEET_NAME}!A1:D10'  # Phạm vi dữ liệu cần đọc
    print(f"Đang đọc dữ liệu từ phạm vi: {range_to_read}")
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=range_to_read).execute()
    values = result.get('values', [])
    if not values:
        print("Không có dữ liệu nào được tìm thấy.")
    else:
        print("Dữ liệu đọc được:")
        for row in values:
            print(row)
except HttpError as e:
    print("Lỗi HTTP khi đọc dữ liệu:", e)
except Exception as e:
    print("Lỗi khác khi đọc dữ liệu:", e)

# Ghi dữ liệu vào Google Sheet
try:
    range_to_write = f'{SHEET_NAME}!A1'  # Vị trí cần ghi dữ liệu
    update_data = {
        "range": range_to_write,
        "values": [["Hello, World!"]]  # Dữ liệu cần ghi
    }
    print(f"Đang ghi dữ liệu vào phạm vi: {range_to_write}")
    sheet.values().update(
        spreadsheetId=SHEET_ID,
        range=range_to_write,
        valueInputOption="RAW",
        body=update_data
    ).execute()
    print("Dữ liệu đã được ghi vào Google Sheet.")
except HttpError as e:
    print("Lỗi HTTP khi ghi dữ liệu:", e)
except Exception as e:
    print("Lỗi khác khi ghi dữ liệu:", e)