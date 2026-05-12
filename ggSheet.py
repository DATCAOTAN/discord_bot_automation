import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# Hàm xác định SHEET_NAME và hàng cần đọc
def get_sheet_and_row(profile_path):
    # Lấy số acc từ đường dẫn profile (ví dụ: ACC (10) -> 10)
    match = re.search(r'ACC \((\d+)\)', profile_path)
    if not match:
        return False
    acc_number = int(match.group(1))
    # Tính hàng cần đọc
    range_start = 1
    row = acc_number - range_start + 2  # +2 vì hàng đầu tiên là tiêu đề
    return  row

# Hàm đọc dữ liệu từ Google Sheets
def read_google_sheet(sheet_name, row, SERVICE_ACCOUNT_FILE,SHEET_ID):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        print("Xác thực thành công.")
    except Exception as e:
        print("Lỗi khi xác thực:", e)
        return False
    try:
        sheet = service.spreadsheets()
        range_to_read = f'{sheet_name}!A{row}:E{row}'  # Đọc dữ liệu từ hàng cụ thể
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=range_to_read).execute()
        values = result.get('values', [])
        if not values:
            return False
    except HttpError as e:
        print("Lỗi HTTP khi đọc dữ liệu:", e)
        return False
    except Exception as e:
        print("Lỗi khác khi đọc dữ liệu:", e)
        return False
    return values[0]  # Trả về hàng dữ liệu
# Hàm cập nhật mật khẩu Discord mới vào Google Sheets  
def edit_sheet_password_discord(sheet_name, row, new_password, SERVICE_ACCOUNT_FILE,SHEET_ID):
    """
    Hàm cập nhật mật khẩu Discord mới vào Google Sheets.
    """
    try:
        # Xác thực Google Sheets API
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        print("Xác thực thành công.")

        # Xác định phạm vi cần cập nhật
        range_to_update = f'{sheet_name}!C{row}'  # Cột C chứa mật khẩu Discord

        # Dữ liệu cần cập nhật
        values = [[new_password]]
        body = {
            'values': values
        }

        # Gửi yêu cầu cập nhật
        result = service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=range_to_update,
            valueInputOption="RAW",
            body=body
        ).execute()

        print(f"Đã cập nhật mật khẩu mới vào Google Sheets: {new_password}")
        return True  # Trả về True nếu cập nhật thành công
    except HttpError as e:
        print(f"Lỗi HTTP khi cập nhật mật khẩu: {e}")
        return False  # Trả về False nếu có lỗi
    except Exception as e:
        print(f"Lỗi khác khi cập nhật mật khẩu: {e}")
        return False  # Trả về False nếu có lỗi
