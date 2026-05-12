import re
import json
import time
import threading
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from googleapiclient.errors import HttpError
import requests
# Cấu hình Google Sheets API
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Hàm xác định SHEET_NAME và hàng cần đọc
def get_sheet_and_row(profile_path):
    # Lấy số acc từ đường dẫn profile (ví dụ: ACC (10) -> 10)
    match = re.search(r'ACC \((\d+)\)', profile_path)
    if not match:
        raise ValueError(f"Không tìm thấy số acc trong đường dẫn: {profile_path}")
    acc_number = int(match.group(1))

    # Xác định SHEET_NAME dựa trên acc_number
    if 1 <= acc_number <= 200:
        sheet_name = "DISCORD 1-200"
        range_start = 1
    elif 201 <= acc_number <= 400:
        sheet_name = "DISCORD 201-400"
        range_start = 201
    elif 401 <= acc_number <= 600:
        sheet_name = "DISCORD 401-600"
        range_start = 401
    elif 601 <= acc_number <= 800:
        sheet_name = "DISCORD 601-800"
        range_start = 601
    else:
        raise ValueError(f"Số acc {acc_number} không nằm trong khoảng hợp lệ.")

    # Tính hàng cần đọc
    row = acc_number - range_start + 2  # +2 vì hàng đầu tiên là tiêu đề
    return sheet_name, row

# Hàm đọc dữ liệu từ Google Sheets
def read_google_sheet(sheet_name, row):
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
    try:
        sheet = service.spreadsheets()
        range_to_read = f'{sheet_name}!A{row}:E{row}'  # Đọc dữ liệu từ hàng cụ thể
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=range_to_read).execute()
        values = result.get('values', [])
        if not values:
            raise ValueError(f"Không tìm thấy dữ liệu tại {sheet_name}, hàng {row}.")
    except HttpError as e:
        print("Lỗi HTTP khi đọc dữ liệu:", e)
    except Exception as e:
        print("Lỗi khác khi đọc dữ liệu:", e)
    return values[0]  # Trả về hàng dữ liệu

# Hàm lấy mã 2FA từ trang web
def get_2fa_token(secret_key):
    try:
        url = f"https://2fa.live/tok/{secret_key}"
        
        # Gửi yêu cầu GET đến API
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        
        # Phân tích JSON để lấy mã token
        response_json = response.json()
        token = response_json.get("token")
        if not token:
            raise ValueError("Không tìm thấy mã token trong phản hồi JSON.")
        
        print(f"Token 2FA: {token}")
        return token
    except Exception as e:
        print(f"Lỗi khi lấy mã 2FA: {e}")
        return None

def wait_load_url(driver):
    while True:
        page_state = driver.execute_script("return document.readyState")
        if page_state == "complete":
            print("Trang đã load xong.")
            break  # Thoát khỏi vòng lặp khi trang đã load xong
        else:
            print("Đang chờ load trang...")
            time.sleep(1)  # Chờ 1 giây trước khi kiểm tra lại
def wait_find_element(driver, xpath,acc_name):
    try:
        while True:
            if not driver.find_elements(By.XPATH, xpath):
                print(f"[{acc_name}] Không tìm thấy Xpath. Đang thử lại...")
                time.sleep(1)
            else:
                print(f"[{acc_name}] Đã tìm thấy Xpath")
                return True  # Thoát khỏi vòng lặp khi tìm thấy Xpath
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi tìm Xpath: {e}")
        driver.save_screenshot(f"{acc_name}_error.png")
        return False
def sign_in_hotmail(driver, email, password,acc_name):

    try:
        # Nhập email vào ô input
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="email" and @id="usernameEntry"]'))
        )
        email_input.send_keys(email)
        print(f"[{acc_name}] Đã nhập email.")

        # Nhấn nút "Next"
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @data-testid="primaryButton"]'))
        )
        next_button.click()
        print(f"[{acc_name}] Đã nhấn nút 'Next'.")
        time.sleep(2)  # Đợi 1 giây trước khi tìm ô mật khẩu

        # Nhập mật khẩu vào ô input
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[ @type="password" and @id="passwordEntry" ] '))
        )
        password_input.send_keys(password)
        print(f"[{acc_name}] Đã nhập mật khẩu.")

        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @data-testid="primaryButton"]'))
        )
        next_button.click()
        print(f"[{acc_name}] Đã nhấn nút 'Next'.")
        time.sleep(2)  # Đợi 1 giây trước khi tìm nút "Sign in"
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @data-testid="primaryButton"]'))
        )
        next_button.click()

       
    except Exception as e:
        print(f"Lỗi khi đăng nhập vào Hotmail: {e}")

#Vượt 2FA       
def input_2fa(driver,acc_name,secret_2fa):
    try:
        two_fa_input= WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="6-digit authentication code"]')))
        print(f"[{acc_name}] Yêu cầu nhập mã 2FA. Đang lấy mã...")
        token = get_2fa_token(secret_2fa)
        if token:
            two_fa_input.send_keys(token)
            try:
                confirm_button =WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and .//div[text()="Confirm"]]')))
                confirm_button.click()
                print(f"[{acc_name}] Đã nhập mã 2FA và xác nhận.")
            except Exception as e:
                print(f"[{acc_name}] Không tìm thấy nút xác nhận mã 2FA. Lỗi: {e}")
                return
        
        else:
            print(f"[{acc_name}] Không thể lấy mã 2FA. Dừng lại.")
            return
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi nhập mã 2FA: {e}")
        driver.save_screenshot(f"{acc_name}_error_2fa.png")
def click_latest_password_reset_email(driver, acc_name, new_password, secret_2fa):
    try:
        # Tìm tất cả các email có chứa "Password Reset Request for Discord"
        emails = driver.find_elements(By.XPATH, '//span[contains(text(), "Password Reset Request for Discord")]')

        if not emails:
            print(f"[{acc_name}] Không tìm thấy email nào chứa 'Password Reset Request for Discord'.")
            return

        # Chọn email gần đây nhất
        latest_email = emails[0]
        print(f"[{acc_name}] Đã tìm thấy email gần đây nhất chứa 'Password Reset Request for Discord'.")

        # Click vào email
        latest_email.click()
        print(f"[{acc_name}] Đã click vào email gần đây nhất.")

        # Chờ trang email load xong
        wait_load_url(driver)

        # Tìm thẻ <a> có text là "Reset Password"
        reset_password_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "Reset Password")]'))
        )
        href = reset_password_link.get_attribute("href")
        print(f"[{acc_name}] Đã lấy được href: {href}")

        # Điều hướng đến URL từ href
        driver.get(href)
        print(f"[{acc_name}] Đã điều hướng đến URL: {href}")

        # Chờ trang "Change Password" load xong
        wait_load_url(driver)

        # Nhập mật khẩu mới
        new_password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="password" and @name="password"]'))
        )
        new_password_input.send_keys(new_password)
        print(f"[{acc_name}] Đã nhập mật khẩu mới: {new_password}")

        # Click vào nút "Change Password"
        change_password_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and .//div[text()="Change Password"]]'))
        )
        change_password_button.click()
        print(f"[{acc_name}] Đã click vào nút 'Change Password'.")
        wait_find_element(driver,'//input[@placeholder="6-digit authentication code"]',acc_name)
        input_2fa(driver,acc_name,secret_2fa)
        return True
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi xử lý email hoặc đổi mật khẩu: {e}")
        driver.save_screenshot(f"{acc_name}_error.png")
        return False
def edit_sheet_password_discord(sheet_name, row, new_password):
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
    except HttpError as e:
        print(f"Lỗi HTTP khi cập nhật mật khẩu: {e}")
    except Exception as e:
        print(f"Lỗi khác khi cập nhật mật khẩu: {e}")



def interact_discord(profile_path, url, acc_name, position, size, geckopath, binary_location, max_restart=6, mission_text="hello"):
    count_restart = 0

    # Xác định SHEET_NAME và hàng cần đọc
    sheet_name, row = get_sheet_and_row(profile_path)
    print(f"[{acc_name}] Sử dụng sheet: {sheet_name}, hàng: {row}")
    nhiem_vu={}
    nhiem_vu['dang_nhap']=False
    nhiem_vu['Find or start a conversation']=False
    nhiem_vu['ApeApefan']=False
    nhiem_vu['click_ApeApefan']=False
    nhiem_vu['Gửi nhiệm vụ']=False
    nhiem_vu['Hoàn thành']=False

    # Lấy dữ liệu từ Google Sheets
    account_data = read_google_sheet(sheet_name, row)
    email = account_data[1]  # Cột B: Email
    password_discord = account_data[2]  # Cột E: Password
    secret_2fa = account_data[3]  # Cột C: 2FA Secret Key
    password_hotmail = account_data[4]  # Cột D: Password Hotmail
    new_password_discord=password_discord+'a'
    try:
            print(f"[{acc_name}] Opening Discord... (Attempt {count_restart + 1})")

            options = Options()
            options.binary_location = binary_location
            options.add_argument("-profile")
            options.add_argument(profile_path)
            options.set_preference("browser.startup.homepage_override.mstone", "ignore")
            options.set_preference("startup.homepage_welcome_url.additional", "about:blank")
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)

            service = Service(executable_path=geckopath)
            driver = webdriver.Firefox(service=service, options=options)

            driver.set_window_size(*size)
            driver.set_window_position(*position)
            driver.get("https://outlook.live.com/mail/0/")

            wait = WebDriverWait(driver, 50)
            time.sleep(3)
            

            while True:
                        print(f"[{acc_name}] Đã chuyển hướng sang Hotmail.")

                        # Vòng lặp kiểm tra xem trang Hotmail đã load xong chưa
                        wait_load_url(driver)
                        time.sleep(5)  # Đợi 1 giây trước khi kiểm tra lại
                        # Kiểm tra URL hiện tại
                        current_url = driver.current_url
                        if "https://outlook.live.com/mail/0/" in current_url:
                            print(f"[{acc_name}] Đã chuyển hướng thành công đến Hotmail.")
                            if click_latest_password_reset_email(driver, acc_name,new_password_discord,secret_2fa)== False:
                                print(f"[{acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...")
                                continue
                            time.sleep(2)
                            nhiem_vu["dang_nhap"]=True
                            edit_sheet_password_discord(sheet_name, row, new_password_discord)
                            print(f"[{acc_name}] Đã click vào email gần đây nhất.")
                            
                        else:
                            print(f"[{acc_name}] URL hiện tại không phải là Hotmail. Đang thực hiện đăng nhập...")
                            driver.get("https://login.live.com/")
                            try:
                                # Tìm thẻ <a> có class="btn"
                                while True:
                                    if not driver.find_elements(By.XPATH, '//input[@type="email" and @id="usernameEntry"]'):
                                        driver.get("https://login.live.com/")

                                        time.sleep(5)  # Chờ 1 giây trước khi kiểm tra lại
                                    else:
                                        print(f"[{acc_name}] Đã tìm thấy thẻ ")
                                        break
                                
                                wait_load_url(driver)
                                time.sleep(1)  # Đợi 1 giây trước khi kiểm tra lại
                                sign_in_hotmail(driver, email, password_hotmail,acc_name)
                                print(f"[{acc_name}] Đã thực hiện đăng nhập vào Hotmail.")
                                time.sleep(1)
                                driver.get("https://outlook.live.com/mail/0/")
                                print(f"[{acc_name}] Đã chuyển hướng thành công đến Hotmail.")
                                if click_latest_password_reset_email(driver, acc_name,new_password_discord,secret_2fa)== False:
                                        print(f"[{acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...")
                                        continue
                                time.sleep(2)
                                nhiem_vu["dang_nhap"]=True
                                edit_sheet_password_discord(sheet_name, row, new_password_discord)
                                print(f"[{acc_name}] Đã click vào email gần đây nhất.")
                            
                                
                                
                            except Exception as e:
                                print(f"[{acc_name}] Lỗi khi tìm thẻ <a> có class='btn': {e}")
                                count_restart += 1
                                continue
                                            
            
    except Exception as e:
        print(f"[{acc_name}] Lỗi: {e}")
        count_restart += 1
    finally:
        try:
            print(f"[{acc_name}] Đang đóng trình duyệt...")
        except:
            pass

    if count_restart > max_restart:
        print(f"[{acc_name}] Đã khởi động lại quá nhiều lần. Dừng lại.")

# Tạo và chạy các thread cho mỗi tài khoản
threads = []
accounts = {
    "acc1": ("D:/profile_new/ACC (1)/Data/profile", "https://discord.com/login", (0, 0), (500, 500), "D:/drivers/acc1/geckodriver.exe", r"D:\profile_new\ACC (1)\App\firefox64\firefox.exe"),
    "acc2": ("D:/profile_new/ACC (2)/Data/profile", "https://discord.com/login", (510, 0), (500, 500), "D:/drivers/acc2/geckodriver.exe", r"D:\profile_new\ACC (2)\App\firefox64\firefox.exe"),
}

for acc, (profile, url, position, size, geckopath, binary_location) in accounts.items():
    t = threading.Thread(target=interact_discord, args=(profile, url, acc, position, size, geckopath, binary_location))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("✅ Tất cả acc đã mở và gửi nhiệm vụ xong!")