import re
import json
import time
import threading
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
import os
import pandas as pd
from excel import excel_write_lock


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
list_count_error={}
list_count_error['sign_in_hotmail']=0
list_count_error['get_sheet_and_row']=0
list_count_error['read_google_sheet']=0
list_count_error['input_2fa']=0
list_count_error['click_latest_password_reset_email']=0
list_count_error['edit_sheet_password_discord']=0
list_count_error['logic_resset_password']=0
list_count_error['wait_for_any_xpath_or_url']=0
list_count_error['wait_find_element_and_load_and_delete_cookies']=0
list_count_error['login']=0
list_count_error['click_find']=0
zoom_body=0

STOP_ALL_LOOPS = False

def stop_all_loops():
    global STOP_ALL_LOOPS
    STOP_ALL_LOOPS = True

def remove_proxy_from_profile(profile_path):
    for fname in ["prefs.js", "user.js"]:
        fpath = os.path.join(profile_path, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Giữ lại các dòng không phải cấu hình proxy
        new_lines = [line for line in lines if not line.strip().startswith('user_pref("network.proxy.')]
        with open(fpath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)


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
    
#Hàm tương tác với Discord
def wait_for_any_xpath_or_url(driver, xpath_list, timeout=130, poll_frequency=0,url=None,reload_time=60):
    """
    Chờ cho đến khi ít nhất 1 trong các xpath trong mảng xuất hiện trên trang (hoặc hết timeout).
    Nếu sau 10s chưa thấy thì reload lại trang.
    Trả về xpath nào xuất hiện đầu tiên, hoặc None nếu hết timeout.
    """
    time_start=0
    end_time = time_start + 130
    reload = reload_time  # Sau 10s sẽ rel
    while not STOP_ALL_LOOPS and time_start<end_time:
        try:
            for xpath in xpath_list:
                print(f"xpath: {xpath}")
                if driver.find_elements(By.XPATH, xpath) :
                    print(f"Đã tìm thấy phần tử với xpath: {xpath}")
                    return xpath
        except Exception as e:
            pass
        if time_start >= reload:
            print("Không tìm thấy phần tử nào sau 10s, reload lại trang...")
            driver.refresh()
            set_zoom(driver, zoom_body)
            reload = time_start+60
        if url is not None and url in driver.current_url:
            print(f"Đã tìm thấy URL: {url}")
            return url
        print(f"dang kta xpath trong:{time_start}s")
        time.sleep(1)
        time_start+=1
    print(f"Không tìm thấy phần tử nào trong {timeout} giây.")
    return None

# Hàm lấy text từ Shadow DOM
def get_shadow_text(driver, shadow_host_selector, shadow_element_selector):
    try:
        # Đợi shadow host xuất hiện
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, shadow_host_selector))
        )
        # Truy cập shadow root
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        if not shadow_root:
            print("Không thể truy cập Shadow DOM. Kiểm tra quyền truy cập hoặc trạng thái của Shadow DOM.")
            return None

        print("Truy cập Shadow DOM thành công.")

        # Tìm phần tử bên trong shadow root
        shadow_element = shadow_root.find_element(By.CSS_SELECTOR, shadow_element_selector)

        # Kiểm tra nội dung của phần tử
        text_content = driver.execute_script("return arguments[0].textContent;", shadow_element)
        inner_text = driver.execute_script("return arguments[0].innerText;", shadow_element)
        print(f"textContent: {text_content}, innerText: {inner_text}")

        # Nếu không có nội dung, kiểm tra và thay đổi trạng thái hiển thị
        if not text_content.strip():
            print("Phần tử không có nội dung. Đang thay đổi trạng thái hiển thị...")
            driver.execute_script("arguments[0].style.visibility = 'visible';", shadow_element)
            driver.execute_script("arguments[0].style.opacity = '1';", shadow_element)
            driver.execute_script("arguments[0].style.display = 'block';", shadow_element)
            time.sleep(1)  # Đợi trạng thái thay đổi

        # Kiểm tra lại nội dung sau khi thay đổi
        text_content = driver.execute_script("return arguments[0].textContent;", shadow_element)
        print(f"textContent sau khi thay đổi: {text_content}")

        if text_content.strip():
            print(f"Text lấy được: {text_content.strip()}")
            return text_content.strip()
        else:
            print("Phần tử không hiển thị hoặc không có nội dung.")
            return None
    except Exception as e:
        print(f"Lỗi khi lấy text từ Shadow DOM: {e}")
        return None
    


#Hàm kiểm tra captcha đã vượt hay chưa            
def check_captcha(driver,acc_name,Listxpath_noCaptcha=None,url=None):
    print
    time_start = 0  # Lấy thời gian bắt đầu
    while not STOP_ALL_LOOPS and  time_start < 100:
        for xpath in Listxpath_noCaptcha:
                print(f"xpath: {xpath}")
                if driver.find_elements(By.XPATH, xpath) :
                    print(f"Đã tìm thấy phần tử với xpath: {xpath}")
                    return True
        if driver.find_elements(By.XPATH, '//div[contains(text(), "Wait! Are you human?")]'):break
        if url is not None and url in driver.current_url:
            print(f"Đã tìm thấy URL: {url}")
            return True
        time_start+=1
        time.sleep(1)
    time_start=0
    while not STOP_ALL_LOOPS and  time_start < 100:
            captcha_element = driver.find_elements(By.XPATH, '//div[contains(text(), "Wait! Are you human?")]')
            if not captcha_element:
                print(f"[{acc_name}] Captcha đã biến mất. Tiếp tục thực hiện.")
                return True  # Thoát khỏi vòng lặp khi captcha không còn
            else:
                print(f"[{acc_name}] Đang chờ captcha biến mất...")
                time.sleep(1)  # Chờ 1 giây trước khi kiểm tra lại
                time_start+=1
    return False  # Nếu đã chờ quá thời gian quy định mà vẫn không biến mất, trả về False

#Đăng nhập vào Hotmail
def sign_in_hotmail(driver, email, password,acc_name):

    try:
        # Nhập email vào ô input
        # Tìm thẻ <a> có class="btn"
        time_start=0  # Lấy thời gian bắt đầu
        while not STOP_ALL_LOOPS and time_start < 60:
            if not driver.find_elements(By.XPATH, '//input[@type="email" and @id="usernameEntry"]'):
                driver.get("https://login.live.com/")
                set_zoom(driver, zoom_body)
                time_start+=5

                time.sleep(5)  # Chờ 1 giây trước khi kiểm tra lại
            else:
                print(f"[{acc_name}] Đã tìm thấy thẻ ")
                break
        while not driver.find_elements(By.XPATH, '//input[ @type="password" and @id="passwordEntry" ] ') and time_start<60 and not STOP_ALL_LOOPS:
            if click_or_mess_xpath(driver,acc_name,'//input[@type="email" and @id="usernameEntry"]',mode="mess",mess=email,x_path_success='//input[@type="email" and @id="usernameEntry" and @value="'+email+'"]') == False:
                print(f"[{acc_name}] Không thể tìm thấy ô nhập email. Đang tải lại trang...")
                list_count_error['sign_in_hotmail']+=1
                return False
            print(f"[{acc_name}] Đã nhập email: {email}")
            # Nhấn nút "Next"
            if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and @data-testid="primaryButton"]',mode="click")==False:
                print(f"[{acc_name}] Không thể tìm thấy nút 'Next'. Đang tải lại trang...")
                list_count_error['sign_in_hotmail']+=1
                return False
            time.sleep(2)  # Chờ 1 giây trước khi kiểm tra lại
            print(f"[{acc_name}] Đã nhấn nút 'Next'.")
        

        # Nhập mật khẩu vào ô input
        password_input = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//input[ @type="password" and @id="passwordEntry" ] '))
        )
        password_input.send_keys(password)
        print(f"[{acc_name}] Đã nhập mật khẩu.")

        if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and @data-testid="primaryButton"]'],130,0.5)==None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy nút 'Next'. Đang tải lại trang...")
            return False

        next_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @data-testid="primaryButton"]'))
        )
        next_button.click()
        print(f"[{acc_name}] Đã nhấn nút 'Next'.")
        if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and @data-testid="primaryButton"]'],130,0.5)==None:
            print(f"[{acc_name}] Không tìm thấy nút 'Next'. Đang tải lại trang...")
            list_count_error['wait_for_any_xpath_or_url']+=1
            return False
        next_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @data-testid="primaryButton"]'))
        )
        next_button.click()
        return True  # Đăng nhập thành công

       
    except Exception as e:
        print(f"Lỗi khi đăng nhập vào Hotmail: {e}")
        return False


#Kiểm tra xem có thể tìm thấy xpath hay không     

    
#Kiểm tra xem có thể tìm thấy xpath hay không và load trang và xoá cookies
def wait_find_element_and_load_and_delete_cookies(driver, xpath, acc_name):
        start_time = 0  # Lấy thời gian bắt đầu
        count = 0  # Biến đếm số lần thử
        count_delete_cookies = 0  # Biến đếm số lần xóa cookies 
        while not STOP_ALL_LOOPS and count_delete_cookies<2:
            if wait_for_any_xpath_or_url(driver,['//input[@placeholder="6-digit authentication code"]','//span[contains(@class, "ms-Pivot-text") and text()="Other"]','//span[contains(text(), "Password Reset Request for Discord")]'],130,0.5)==None:
                elapsed_time =  start_time  # Tính thời gian đã trôi qua
                print(f"[{acc_name}] Không tìm thấy Xpath:{xpath}. Đang thử lại... (Đã chờ {int(elapsed_time)} giây)")
                if count>=3:
                    print(f"[{acc_name}] Đã thử 3 lần mà không tìm thấy Xpath:{xpath}. Đang xóa cookies và tải lại trang...")
                    driver.delete_all_cookies()
                    count=0  # Đặt lại biến đếm
                    count_delete_cookies+=1  # Tăng biến đếm xóa cookies
                    driver.refresh()  # Tải lại trang hiện tại
                    set_zoom(driver, zoom_body)
                    continue
                if elapsed_time > 20:  # Nếu đã chờ hơn 10 giây
                    print(f"[{acc_name}] Đã chờ hơn 10 giây. Đang tải lại trang...")
                    count += 1  # Tăng biến đếm
                    driver.refresh()  # Tải lại trang hiện tại
                    set_zoom(driver, zoom_body)
                    start_time = 0  # Đặt lại thời gian bắt đầu
                    continue
                start_time+=1
                time.sleep(1)  # Chờ 1 giây trước khi kiểm tra lại
            else:
                print(f"[{acc_name}] Đã tìm thấy Xpath:{xpath}")
                return True  # Thoát khỏi vòng lặp khi tìm thấy Xpath
        return False  # Không tìm thấy Xpath sau 2 lần xóa cookies

    
#Vượt 2FA       
def input_2fa(driver,acc_name,secret_2fa):
    try:
        if wait_for_any_xpath_or_url(driver,['//input[@placeholder="6-digit authentication code"]'],130,0.5)==None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy ô nhập mã 2FA. Đang tải lại trang...")
            return False  # Không tìm thấy ô nhập mã 2FA
        
        two_fa_input= WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="6-digit authentication code"]')))
        print(f"[{acc_name}] Yêu cầu nhập mã 2FA. Đang lấy mã...")
        token = get_2fa_token(secret_2fa)
        if token:
            two_fa_input.send_keys(token)
            try:
                if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and .//div[text()="Confirm"]]'],130,0.5)==None:
                    list_count_error['wait_for_any_xpath_or_url']+=1
                    print(f"[{acc_name}] Không tìm thấy nút xác nhận mã 2FA. Đang tải lại trang...")
                    return False
                confirm_button =WebDriverWait(driver,60).until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and .//div[text()="Confirm"]]')))
                confirm_button.click()
                print(f"[{acc_name}] Đã nhập mã 2FA và xác nhận.")
                return True  # Đã nhập mã 2FA thành công
            
            except Exception as e:
                print(f"[{acc_name}] Không tìm thấy nút xác nhận mã 2FA. Lỗi: {e}")
                return False
        
        else:
            print(f"[{acc_name}] Không thể lấy mã 2FA. Dừng lại.")
            return False  # Không thể lấy mã 2FA
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi nhập mã 2FA: {e}")
        return False

def click_or_mess_xpath(driver,acc_name,xpath,mode="click",mess="",x_path_success=None,count_restarmax=5,load_page=0):
    count_restar=0
    load=load_page
    print(f"[{acc_name}] Đang tìm phần tử với XPath: {xpath} và mode: {mode}")
    print(f'[{acc_name}] mess: {mess} success_xpath: {x_path_success}')
    while not STOP_ALL_LOOPS and count_restar<count_restarmax:
        if wait_for_any_xpath_or_url(driver,[xpath])==False:
            print(f"[{acc_name}] Không tìm thấy phần tử với XPath: {xpath}. Đang thử lại...")
            return False  # Không tìm thấy phần tử với XPath sau 60 giây
        try:
            if mode=="click":
                element = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                element.click()
                print(f"[{acc_name}] Đã click vào phần tử với XPath: {xpath}")
            elif mode=="mess":
                element=driver.find_element(By.XPATH, xpath)
                print(f"[{acc_name}] Đã click vào phần tử với XPath: {xpath} để nhập văn bản.")
                element.send_keys(mess)
                print(f"[{acc_name}] Đã nhập văn bản: {mess}")
                print(f"[{acc_name}] Đã tìm thấy phần tử với XPath: {xpath}")
            
            if x_path_success is not None:
                isLoad(driver)
                if driver.find_elements(By.XPATH, x_path_success) :
                    print(f"[{acc_name}] Đã tìm thấy phần tử với XPath thành công: {x_path_success}.")
                    return True
                print(f"[{acc_name}] Không tìm thấy phần tử với XPath thành công: {x_path_success}. Đang tải lại trang...")
                driver.refresh()  # Tải lại trang hiện tại
            return True  # Click hoặc nhập văn bản thành công
        except Exception as e:
            count_restar+=1
            if count_restar>load:
                print(f"[{acc_name}] Đã thử {count_restar} lần mà không tìm thấy phần tử với XPath: {xpath}. Đang tải lại trang...")
                driver.refresh()
                load=count_restar+load_page  # Đặt lại thời gian bắt đầu
            print(f"[{acc_name}] Lỗi khi click hoặc tìm phần tử với XPath: {xpath}. Lỗi: {e}")
    return False  # Không tìm thấy phần tử sau 60 giây
            
 # Hàm click vào email mới nhất và đổi mật khẩu       
def click_latest_password_reset_email(driver, acc_name, new_password, secret_2fa):
    if wait_find_element_and_load_and_delete_cookies(driver,'//input[@placeholder="Search"]',acc_name) == False:
        print(f"[{acc_name}] chưa load xong trang hotmail.")
        list_count_error['click_latest_password_reset_email']+=1
        return False
    if( driver.find_elements(By.XPATH, '//span[contains(@class, "ms-Pivot-text") and text()="Other"]')):
        print(f"[{acc_name}] Đã tìm thấy thẻ <span> có class 'ms-Pivot-text' và text 'Other'.")
        isLoad(driver)
        if click_or_mess_xpath(driver,acc_name,'//span[contains(@class, "ms-Pivot-text") and text()="Other"]',mode="click",x_path_success='//span[contains(text(), "Password Reset Request for Discord")]',load_page=10)==False:
            print(f"[{acc_name}] Không thể click vào nút 'Other'. Đang tải lại trang...")
            list_count_error['click_latest_password_reset_email']+=1
            return False
    try:
        
    
        # Click vào email

        while True and not STOP_ALL_LOOPS:
            if wait_for_any_xpath_or_url(driver,['//span[contains(text(), "Password Reset Request for Discord")]'],130,0.5)==None:
                list_count_error['wait_for_any_xpath_or_url']+=1
                print(f"[{acc_name}] Không tìm thấy email nào chứa 'Password Reset Request for Discord'. Đang tải lại trang...")
                return False
            emails = driver.find_elements(By.XPATH, '//span[contains(text(), "Password Reset Request for Discord")]')
            if not emails:
                print(f"[{acc_name}] Không tìm thấy email nào chứa 'Password Reset Request for Discord'.")
                return False

            # Chọn email gần đây nhất
            latest_email = emails[0]
            print(f"[{acc_name}] Đã tìm thấy email gần đây nhất chứa 'Password Reset Request for Discord'.")
            try:
                latest_email.click()
                break  # Thoát khỏi vòng lặp nếu click thành công
            except Exception as e:
                print(f"[{acc_name}] Lỗi khi click vào email: {e}. Đang thử lại...")
                time.sleep(1)
                driver.refresh()  # Tải lại trang hiện tại
                
        print(f"[{acc_name}] Đã click vào email gần đây nhất.")

        if wait_for_any_xpath_or_url(driver,['//a[contains(text(), "Reset Password")]'],130,0.5)==None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy thẻ <a> có text 'Reset Password'. Đang tải lại trang...")
            return False

        

        # Tìm thẻ <a> có text là "Reset Password"
        reset_password_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(text(), "Reset Password")]'))
        )
        href = reset_password_link.get_attribute("href")
        print(f"[{acc_name}] Đã lấy được href: {href}")

        # Điều hướng đến URL từ href
        driver.get(href)
        set_zoom(driver, zoom_body)
        print(f"[{acc_name}] Đã điều hướng đến URL: {href}")
        time_start=0  # Lấy thời gian bắt đầu
        while not driver.find_elements(By.XPATH, '//input[@placeholder="6-digit authentication code"]')and time_start<4 and not STOP_ALL_LOOPS:
            if click_or_mess_xpath(driver,acc_name,'//input[@type="password" and @name="password"]',mode="mess",mess=new_password,x_path_success=f'//input[@type="password" and @name="password" and @value="{new_password}"]')==False:
                print(f"[{acc_name}] Không thể tìm thấy ô nhập mật khẩu mới. Đang tải lại trang...")
                list_count_error['click_latest_password_reset_email']+=1
                continue
            print(f"[{acc_name}] Đã nhập mật khẩu mới: {new_password}")

            # Click vào nút "Change Password"
            
            if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and .//div[text()="Change Password"]]'):
                print(f"[{acc_name}] Đã click vào nút 'Change Password'.")
            else:
                print(f"[{acc_name}] Không thể click vào nút 'Change Password'. Đang tải lại trang...")
                list_count_error['click_latest_password_reset_email']+=1
                continue
            print(f"[{acc_name}] Đã click vào nút 'Change Password'.")
            time.sleep(1)
            time_start+=1
        
        print(f"[{acc_name}] Đã nhập mật khẩu mới và click vào nút 'Change Password'.")
        if input_2fa(driver,acc_name,secret_2fa)== False:
            print(f"[{acc_name}] Không thể nhập mã 2FA. Đang tải lại trang...")
            list_count_error['input_2fa']+=1
            return False
        return True
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi xử lý email hoặc đổi mật khẩu: {e}")
        return False

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


def wait_for_element_and_proceed(driver, acc_name, xpath, callback):
    """
    Hàm chạy trong luồng riêng để chờ phát hiện phần tử và thực hiện bước tiếp theo.
    """
    try:
        print(f"[{acc_name}] Đang chờ phát hiện thẻ với XPath: {xpath}")
        while True:
            if driver.find_elements(By.XPATH, xpath):
                print(f"[{acc_name}] Đã phát hiện thẻ với XPath: {xpath}")
                break
            else:
                print(f"[{acc_name}] Chưa phát hiện thẻ. Đang chờ...")
                time.sleep(1)  # Chờ 1 giây trước khi kiểm tra lại

        # Khi phát hiện thẻ, thực hiện callback
        callback()
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi chờ phát hiện thẻ: {e}")

def interact_with_web(driver, acc_name, email, password_hotmail):
    """
    Hàm chính để thực hiện các bước tiếp theo sau khi phát hiện thẻ.
    """
    try:
        btn_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@id, "action-oc5b26")]'))
        )
        href_value = btn_element.get_attribute("href")
        print(f"[{acc_name}] Giá trị href của thẻ <a>: {href_value}")

        # Chuyển hướng đến URL từ href
        driver.get(href_value)
        print(f"[{acc_name}] Đã chuyển hướng đến URL: {href_value}")

        # Vòng lặp kiểm tra xem trang đã load xong chưa
        

        time.sleep(1)  # Đợi 1 giây trước khi kiểm tra lại
        sign_in_hotmail(driver, email, password_hotmail)
        print(f"[{acc_name}] Đã thực hiện đăng nhập vào Hotmail.")
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi thực hiện các bước tiếp theo: {e}")

# Sử dụng luồng riêng để chờ phát hiện thẻ
def start_waiting_for_element(driver, acc_name, email, password_hotmail):
    xpath = '//a[contains(@id, "action-oc5b26")]'
    thread = threading.Thread(
        target=wait_for_element_and_proceed,
        args=(driver, acc_name, xpath, lambda: interact_with_web(driver, acc_name, email, password_hotmail))
    )
    thread.start()

#Loogic reset password
def logic_resset_password(driver, acc_name, email, password_hotmail, new_password_discord, secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID):
        print(f"[{acc_name}] Đang bị reset password.")
        try:
            # Chờ và nhấn vào nút "Forgot your password?"
                # Đợi 1 giây trước khi tìm nút
            
            time_reset=0  # Lấy thời gian bắt đầu
            while not STOP_ALL_LOOPS and time_reset<2 and not driver.find_elements(By.XPATH,  '//button[@type="submit" and .//div[text()="Okay"]]'):
                if wait_for_any_xpath_or_url(driver,['//button[@type="button" and .//div[text()="Forgot your password?"]]'],acc_name)==None:
                    list_count_error['wait_for_any_xpath_or_url']+=1
                    print(f"[{acc_name}] Không tìm thấy nút 'Forgot your password?'. Đang tải lại trang...")
                    return False
                reset_password_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@type="button" and .//div[text()="Forgot your password?"]]'))
                )
                 # Đợi 1 giây trước khi click vào nút
                time.sleep(2)
                try:
                    reset_password_button.click()
                except Exception as e:     
                    print(f"[{acc_name}] Lỗi khi click vào nút 'Forgot your password?': {e}")
                time.sleep(2)
                try:
                    reset_password_button.click()
                except:
                    print("lỗi click")
                print(f"[{acc_name}] Đã click vào nút 'Forgot your password?'.")
                #Check xem có captcha không
                if check_captcha(driver,acc_name,['//button[@type="submit" and .//div[text()="Okay"]]'])== False:
                    print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
                    return False

                # Chờ nút "Okay" xuất hiện
                print(f"[{acc_name}] Đang chờ nút 'Okay' xuất hiện...")
                if(wait_for_any_xpath_or_url(driver,['//button[@type="submit" and .//div[text()="Okay"]]'],acc_name)):
                    print(f"[{acc_name}] Đã tìm thấy nút 'Okay'.")
                    break  # Thoát khỏi vòng lặp khi tìm thấy nút
                driver.refresh()
                time_reset+=1
               
                # Nhấn nút "Okay"
            if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and .//div[text()="Okay"]]',mode="click")== False:
                print(f"[{acc_name}] Không thể click vào nút 'Okay'. Đang tải lại trang...")
                list_count_error['click_latest_password_reset_email']+=1
                return False
            print("Đã click vào nút 'Okay'.")
            
            driver.get("https://outlook.live.com/mail/0/")
            time.sleep(6)
            set_zoom(driver, zoom_body)
            print(f"[{acc_name}] Đã chuyển hướng sang Hotmail.")
            # Kiểm tra URL hiện tại
            current_url = driver.current_url
            if "https://outlook.live.com/mail/0/" in current_url:
                print(f"[{acc_name}] Đã chuyển hướng thành công đến Hotmail.")
                if click_latest_password_reset_email(driver, acc_name,new_password_discord,secret_2fa)== False:
                    print(f"[{acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...")
                    list_count_error['click_latest_password_reset_email']+=1
                    return False
                time.sleep(1)
                if edit_sheet_password_discord(sheet_name, row, new_password_discord,SERVICE_ACCOUNT_FILE,SHEET_ID)== False:
                    print(f"[{acc_name}] Không thể cập nhật mật khẩu trong Google Sheets. Đang thử lại...")
                    list_count_error['edit_sheet_password_discord']+=1
                    return False
                print(f"{acc_name}] Đã thay đổi password trong gg_sheet.")
                return True  # Đã click vào email thành công
                
            else:
                print(f"[{acc_name}] URL hiện tại không phải là Hotmail. Đang thực hiện đăng nhập...")
                driver.get("https://login.live.com/")
                set_zoom(driver, zoom_body)
                try:

                    if sign_in_hotmail(driver, email, password_hotmail,acc_name)== False:
                        print(f"[{acc_name}] Không thể đăng nhập vào Hotmail. Đang thử lại...")
                        list_count_error['sign_in_hotmail']+=1
                        return False
                    print(f"[{acc_name}] Đã thực hiện đăng nhập vào Hotmail.")
                    time.sleep(1)
                    driver.get("https://outlook.live.com/mail/0/")
                    time.sleep(1)
                    print(f"[{acc_name}] Đã chuyển hướng thành công đến Hotmail.")
                    if click_latest_password_reset_email(driver, acc_name,new_password_discord,secret_2fa)== False:
                            print(f"[{acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...")
                            list_count_error['click_latest_password_reset_email']+=1
                            return False
                    time.sleep(1)                
                    if edit_sheet_password_discord(sheet_name, row, new_password_discord,SERVICE_ACCOUNT_FILE,SHEET_ID)== False:
                        print(f"[{acc_name}] Không thể cập nhật mật khẩu trong Google Sheets. Đang thử lại...")
                        list_count_error['edit_sheet_password_discord']+=1
                        return False
                    print(f"{acc_name}] Đã thay đổi password trong gg_sheet.")
                    return True  # Đã click vào email thành công
            
                                                                
                except Exception as e:
                    print(f"[{acc_name}] Lỗi khi tìm thẻ <a> có class='btn': {e}")
                    return False
                                                
        except Exception as e:
            print(f"[{acc_name}] Lỗi khi xử lý nút 'Forgot your password?': {e}")

            return False
# Hàm logic đăng nhập và reset mật khẩu Discord
def logic_login_and_reset_password_discord(driver, acc_name,wait,email,password_discord,password_hotmail,new_password_discord,secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID):
            while not STOP_ALL_LOOPS and not driver.find_elements(By.XPATH, '//input[@placeholder="6-digit authentication code"]') and not driver.find_elements(By.XPATH, "//label[contains(text(), 'Email or Phone Number') and .//span[.//span]]") and not driver.find_elements(By.XPATH, "//div[contains(text(), 'Find or start a conversation')]"):
                print(f"[{acc_name}] Đang chờ trang Discord load xong...")
                if(wait_for_any_xpath_or_url(driver, ['//button[@type="button" and .//div[text()="Log in"]]', '//button[@type="submit" and .//div[text()="Log In"]]'], 130, 0.5)==None):           
                    print(f"[{acc_name}] Không tìm thấy nút 'Log in' hoặc 'Log In'. Đang thử lại...")
                    list_count_error['wait_for_any_xpath_or_url']+=1
                    return False
                print(f"[{acc_name}] Đã tìm thấy nút 'Log in' hoặc 'Log In'.")
                if(driver.find_elements(By.XPATH, '//button[@type="button" and .//div[text()="Log in"]]')):
                    print(f"[{acc_name}] Đã tìm thấy nút 'Log in' loai button.")
                    element=driver.find_element(By.XPATH, '//button[@type="button" and .//div[text()="Log in"]]')
                    element.click()

                print(f"[{acc_name}] Đã tìm thấy nút 'Log In'.")
                login_button =  wait.until(EC.presence_of_element_located((By.XPATH,  '//button[@type="submit" and .//div[text()="Log In"]]')))
                print(f"[{acc_name}] Chưa đăng nhập. Đang thực hiện đăng nhập...")
                email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
                password_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
                email_input.send_keys(email)
                password_input.send_keys(password_discord)
                login_button.click()
                if check_captcha(driver,acc_name,['//input[@placeholder="6-digit authentication code"]',"//label[contains(text(), 'Email or Phone Number') and .//span[.//span]]","//div[contains(text(), 'Find or start a conversation')]"]) == False:
                    print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
                    return False
                time.sleep(2)
            # Kiểm tra xem có yêu cầu nhập mã 2FA không
            
            if driver.current_url == "https://discord.com/channels/@me":
                    print(f"[{acc_name}] Đã đăng nhập mà không cần mã 2FA.")
                    return True
            else:
                if driver.find_elements(By.XPATH, "//label[contains(text(), 'Email or Phone Number') and .//span[.//span]]"):
                        if logic_resset_password(driver, acc_name, email, password_hotmail, new_password_discord, secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID)== False:
                            print(f"[{acc_name}] Không thể reset password. ")
                            list_count_error['logic_resset_password']+=1
                            return False
                        else:
                            print(f"[{acc_name}] Đã reset password thành công.")
                            return True
            
            
                else:
                    if input_2fa(driver, acc_name, secret_2fa) == False:
                        print(f"[{acc_name}] Không thể nhập mã 2FA. Đang thử lại...")
                        list_count_error['input_2fa']+=1
                        return False
#Join discord
def logic_join_url_discord(driver, acc_name, url, load_max=3):
    count_load = 0
    while not STOP_ALL_LOOPS and count_load < load_max:
        driver.get(url)
        set_zoom(driver, zoom_body)
        # Chờ nút Accept Invite xuất hiện
        if wait_for_any_xpath_or_url(driver, ["//button[.//div[text()='Accept Invite']]"], 130, 0.5) is None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy nút 'Accept Invite'. Đang tải lại trang...")
            return False
        accept_invite_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='Accept Invite']]"))
        )
        accept_invite_button.click()
        if check_captcha(driver, acc_name,[
                "//button[.//div[contains(text(), 'Continue to Discord')]]",
            ], url="https://discord.com/channels") == False:
            print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
            return False
        print(f"[{acc_name}] Đã click vào nút 'Accept Invite'.")

        # Chờ nút Continue to Discord hoặc Accept Invite xuất hiện lại, hoặc chuyển hướng thành công
        if wait_for_any_xpath_or_url(
            driver,
            [
                "//button[.//div[contains(text(), 'Continue to Discord')]]",
                "//button[.//div[text()='Accept Invite']]"
            ],
            130, 0.5, url="https://discord.com/channels"
        ) is None:
            print(f"[{acc_name}] Không tìm thấy nút 'Continue to Discord'.")
            list_count_error['wait_for_any_xpath_or_url']+=1
            return False

        current_url = driver.current_url
        if "https://discord.com/channels" in current_url:
            print(f"[{acc_name}] Đã chuyển hướng thành công đến Discord.")
            return True

        # Nếu vẫn còn nút Accept Invite thì thử lại
        try:
            accept_invite_button_element = driver.find_element(By.XPATH, "//button[.//div[text()='Accept Invite']]")
            if accept_invite_button_element:
                count_load += 1
                continue
        except:
            pass

        # Nếu có nút Continue to Discord thì click
        try:
            continue_discord_button_element = driver.find_element(By.XPATH, "//button[.//div[contains(text(), 'Continue to Discord')]]")
            if continue_discord_button_element:
                continue_discord_button_element.click()
                if check_captcha(driver, acc_name, [
                        "//button[.//div[contains(text(), 'Continue to Discord')]]",
                    ]) == False:
                    print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
                    return False
                time.sleep(6)
                if wait_for_any_xpath_or_url(
                    driver,
                    [
                        "//button[.//div[contains(text(), 'Continue to Discord')]]",
                        "//button[.//div[text()='Accept Invite']]"
                    ],
                    30, 0.5, url="https://discord.com/channels"
                ) is None:
                    print(f"[{acc_name}] Không tìm thấy nút 'Continue to Discord'.")
                    list_count_error['wait_for_any_xpath_or_url']+=1
                    return False
                current_url = driver.current_url
                if "https://discord.com/channels" in current_url:
                    print(f"[{acc_name}] Đã chuyển hướng thành công đến Discord.")
                    return True
                else:
                    count_load += 1
                    print(f"[{acc_name}] URL hiện tại không phải là Discord. Đang tải lại trang...")
                    continue
        except:
            pass

        count_load += 1
    return False



    
    

def interact_discord(profile_path, url, acc_name, position, size, geckopath, binary_location, mission_text="hello", proxy=None, SERVICE_ACCOUNT_FILE=None, SHEET_ID=None,sheet_name=None, zoom=50, size_goc=None,thread_index=0,restart_max=1000,list_url=None,log_file=None,mode="manual"):
    restart_count=0
    zoom_body=zoom
    list_join_success=[]
    nhiem_vu={}
    nhiem_vu['Find or start a conversation']=False
    nhiem_vu['ApeApefan']=False
    nhiem_vu['click_ApeApefan']=False
    nhiem_vu['Gửi nhiệm vụ']=False
    nhiem_vu['Hoàn thành']=False

    text_error=""
    while not STOP_ALL_LOOPS and restart_count<restart_max:
        # Xác định SHEET_NAME và hàng cần đọc
        # Lấy dữ liệu từ Google Sheets
        flag_closeFireFox=False
        nhiem_vu['dang_nhap']=False
        row = get_sheet_and_row(profile_path)
        if sheet_name==None:
            print(f"[{acc_name}] Không thể lấy tên sheet và hàng từ profile. Đang thử lại...")
            list_count_error['get_sheet_and_row']+=1
            text_error="Không thể lấy tên sheet và hàng từ profile."
            write_error_to_file(log_file[0],log_file[1], acc_name, text_error)
            return False
        account_data = read_google_sheet(sheet_name, row, SERVICE_ACCOUNT_FILE, SHEET_ID)
        if account_data==False:
            print(f"[{acc_name}] Không thể đọc dữ liệu từ Google Sheets. Đang thử lại...")
            list_count_error['read_google_sheet']+=1
            text_error="Không thể đọc dữ liệu từ Google Sheets."
            write_error_to_file(log_file[0],log_file[1], acc_name, text_error)
            return False
        
        
        
        remove_proxy_from_profile(profile_path)
        try:
                print(f"[{acc_name}] Opening Discord)")
                options = Options()
                options.binary_location = binary_location
                options.add_argument("-profile")
                options.add_argument(profile_path)
                options.set_preference("browser.startup.homepage_override.mstone", "ignore")
                options.set_preference("startup.homepage_welcome_url.additional", "about:blank")
                options.set_preference("dom.webdriver.enabled", False)
                options.set_preference("useAutomationExtension", False)
                # Cấu hình proxy hoàn chỉnh
                if proxy:
                        # HTTP/HTTPS proxy: host:port
                        host, port = proxy.split(":", 1)
                        print(f"[{acc_name}] Dùng proxy HTTP/HTTPS: {host}:{port}")
                        options.set_preference("network.proxy.type", 1)
                        options.set_preference("network.proxy.http", host)
                        options.set_preference("network.proxy.http_port", int(port))
                        options.set_preference("network.proxy.ssl", host)
                        options.set_preference("network.proxy.ssl_port", int(port))
                        options.set_preference("network.proxy.no_proxies_on", "")
                else:
                    print(f"[{acc_name}] Sử dụng proxy hệ thống.")
                

                service = Service(executable_path=geckopath)
                driver = webdriver.Firefox(service=service, options=options)
                

                driver.set_window_size(size_goc[0],size_goc[1])
                print(f"[{acc_name}] Kích thước cửa sổ: {driver.get_window_size()}")
                driver.set_window_position(thread_index*driver.get_window_size()['width'],0)
                  # 50% scale (0.5), 1.0 là mặc định
                driver.get("https://discord.com/login")
                set_zoom(driver, zoom_body)
                print(f"[{acc_name}] Đã mở Discord.")
                if isLoad(driver) == False:
                    flag_closeFireFox=True
                    print(f"[{acc_name}] Trang chưa load xong. Đang thử lại...")
                    list_count_error['isLoad']+=1
                    text_error="Trang chưa load xong."
               
                print("da load xong")
                wait = WebDriverWait(driver, 60)
                set_zoom(driver, zoom_body)
                while True and flag_closeFireFox==False and not STOP_ALL_LOOPS:
                    try:
                        # Lấy handle của tab hiện tại
                        
                        
                        print(f"[{acc_name}] Trang đã load xong.")


                        email = account_data[1]  # Cột B: Email
                        password_discord = account_data[2]  # Cột E: Password
                        secret_2fa = account_data[3]  # Cột C: 2FA Secret Key
                        password_hotmail = account_data[4]  # Cột D: Password Hotmail
                        new_password_discord=password_discord+"a"
                        print(f"[{acc_name}] Sử dụng sheet: {sheet_name}, hàng: {row}")  
                        print(f"[{acc_name}] Bắt đầu tương tác với Discord.")
                       
                        
                        current_tab = driver.current_window_handle
                        driver.switch_to.window(current_tab)  # Chuyển về tab hiện tại
                        current_url = driver.current_url
                        
                            # Chỉ kiểm tra nếu URL khác với Discord
                        if "about:logins"  in current_url:
                            print(f"[{acc_name}] Đang thoát profile.")
                            print("Dừng kiểm tra và thoát.")
                            driver.quit()
                            return 1  # Thoát khỏi vòng lặp
                        
                        elif "preferences"  in current_url:
                                nhiem_vu['dang_nhap']=False
    
                                driver.get("https://discord.com/login")
                                set_zoom(driver, zoom_body)
                                if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and .//div[text()="Log In"]]','//div[contains(text(), "Find or start a conversation")]','//button[@type="submit" and .//div[text()="Log in"]]'],130,0.5)==None:
                                    print(f"[{acc_name}] Không tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Restarting...")
                                    list_count_error['wait_for_any_xpath_or_url']+=1
                                    continue
                                
                                if("https://discord.com/login" not in driver.current_url):
                                    print(f"[{acc_name}] Đã chuyển hướng đến URL: {driver.current_url}")
                                    continue

                                if logic_login_and_reset_password_discord(driver, acc_name,wait,email,password_discord,password_hotmail,new_password_discord,secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID)==False:
                                    print(f"[{acc_name}] Không thể đăng nhập. Đang thử lại...")
                                    list_count_error['login']+=1
                                    flag_closeFireFox=True
                                    break
                                nhiem_vu['dang_nhap']=True
                                
                                                    
                        else:
                            print(f"[{acc_name}] Bỏ qua kiểm tra.")
                    except Exception as e:
                        print(f"[{acc_name}] Lỗi: {e}")
                        print("Tao cố ý")
                        flag_closeFireFox=True
                        break
                        
                    if nhiem_vu['dang_nhap'] == False:
                        print("chuwa dang nhap")
                        isLoad(driver)
                        print(driver.current_url)
                        if "https://discord.com/channels/@me" in driver.current_url :
                            nhiem_vu['dang_nhap']=True
                            print(f"[{acc_name}] Đã chuyển hướng thành công đến Discord.")
                        elif nhiem_vu['dang_nhap']==False and   "https://discord.com/login" in driver.current_url:
                            if logic_login_and_reset_password_discord(driver, acc_name,wait,email,password_discord,password_hotmail,new_password_discord,secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID)==False:
                                print(f"[{acc_name}] Không thể đăng nhập. Đang thử lại...")
                                list_count_error['login']+=1
                                flag_closeFireFox=True
                                break
                            nhiem_vu['dang_nhap']=True
                    else:
                        print("da dang nhap thanh cong")
                    while not STOP_ALL_LOOPS and nhiem_vu['Hoàn thành'] == False and mode=="manual" and nhiem_vu['dang_nhap']==True:    

                        if nhiem_vu['Find or start a conversation'] == False:
                            try:
                                if click_or_mess_xpath(driver,acc_name,'//div[contains(text(), "Find or start a conversation")]',load_page=10)==False:
                                    print(f"[{acc_name}] Không thể click vào nút 'Find or start a conversation'. Đang thử lại...")
                                    list_count_error['click_find']+=1
                                    if(list_count_error['click_find']>10):
                                        print(f"[{acc_name}] Không thể click vào nút 'Find or start a conversation'. Đang thử lại...")
                                        list_count_error['click_find']=0
                                    continue
                                print(f"[{acc_name}] Đã click vào nút 'Find or start a conversation'.")
                                nhiem_vu['Find or start a conversation']=True
                               
                            except Exception as e:
                                print(f"[{acc_name}] Không tìm thấy nút 'Find or start a conversation'. Restarting... Error: {e}")
                                list_count_error['click_find']+=1
                                if(list_count_error['click_find']>10):
                                    print(f"[{acc_name}] Không thể click vào nút 'Find or start a conversation'. Đang thử lại...")
                                    list_count_error['click_find']=0
                                continue
                    

                        # Gửi nội dung nhiệm vụ vào chat
                        elif nhiem_vu['ApeApefan'] == False:
                            try:
                                if click_or_mess_xpath(driver,acc_name,'//input[@aria-label="Quick switcher"]',mode="mess",mess="ApeApefan",x_path_success='//input[@aria-label="Quick switcher" and @value="ApeApefan"]')==False:
                                    print(f"[{acc_name}] Không thể click vào thanh tìm kiếm. Đang thử lại...")
                                    list_count_error['click_quick_switcher']+=1
                                    if(list_count_error['click_quick_switcher']>10):
                                        print(f"[{acc_name}] Không thể click vào thanh tìm kiếm. Đang thử lại...")
                                        list_count_error['click_quick_switcher']=0
                                    continue
                                print(f"[{acc_name}] Đã click vào thanh tìm kiếm.")
                                nhiem_vu['ApeApefan']=True
                                print(f"[{acc_name}] Đã nhập 'ApeApefan' vào thanh tìm kiếm.")
                            except Exception as e:
                                print(f"[{acc_name}] Không tìm thấy thanh tìm kiếm. Restarting... Error: {e}")
                                continue
                        elif nhiem_vu['click_ApeApefan'] == False:
                            try:
                                if click_or_mess_xpath(driver,acc_name,'(//div[@aria-label="ApeApefan, User, apeapefan"])[1]',mode="click")==False:
                                    print(f"[{acc_name}] Không thể click vào server đầu tiên. Đang thử lại...")
                                    list_count_error['click_ApeApefan']+=1
                                    if(list_count_error['click_ApeApefan']>10):
                                        print(f"[{acc_name}] Không thể click vào server đầu tiên. Đang thử lại...")
                                        list_count_error['click_ApeApefan']=0
                                    continue
                                nhiem_vu['click_ApeApefan']=True
                                print(f"[{acc_name}] Đã tìm thấy và click vào server đầu tiên.")
                            except Exception as e:
                                print(f"[{acc_name}] Không tìm thấy server đầu tiên. Restarting... Error: {e}")
                                continue

                        elif nhiem_vu['Gửi nhiệm vụ'] == False:
                            try:
                                if wait_for_any_xpath_or_url(driver,['//div[@role="textbox" and @contenteditable="true"]'],130,0.5)==None:
                                    print(f"[{acc_name}] Không tìm thấy ô chat. Restarting...")
                                    list_count_error['wait_for_any_xpath_or_url']+=1
                                    flag_closeFireFox=True
                                    break
                                message_box = wait.until(EC.presence_of_element_located((
                                    By.XPATH, '//div[@role="textbox" and @contenteditable="true"]'
                                )))
                                message_box.send_keys(mission_text)                     
                                message_box.send_keys(Keys.ENTER)
                                nhiem_vu['Gửi nhiệm vụ']=True
                                nhiem_vu['Hoàn thành']=True
                                print(f"[{acc_name}] Đã gửi nhiệm vụ xong!")
                            except Exception as e:
                                print(f"[{acc_name}] Lỗi khi gửi tin nhắn: {e}")
                                driver.save_screenshot(f"{acc_name}_error_message.png")
                                continue
                    if mode=="auto" and len(list_url)>0:
                        count_join_success=0
                        for url in list_url:
                            if url not in list_join_success:
                                if  logic_join_url_discord(driver,acc_name,url)== False:
                                    print(f"[{acc_name}] Không thể tham gia vào URL: {url}. Đang thử lại...")
                                    continue
                                else:
                                    driver.get("https://discord.com/login")
                                    if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and .//div[text()="Log In"]]','//div[contains(text(), "Find or start a conversation")]','//button[@type="submit" and .//div[text()="Log in"]]'],130,0.5,url="https://discord.com/channels/@me")==None:
                                        print(f"[{acc_name}] Không tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Restarting...")
                                        list_count_error['wait_for_any_xpath_or_url']+=1
                                        continue
                                    print("Đã load xong")
                                    if "https://discord.com/channels/@me" not in driver.current_url and logic_login_and_reset_password_discord(driver, acc_name,wait,email,password_discord,password_hotmail,new_password_discord,secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID)==False:
                                        print(f"[{acc_name}] Không thể đăng nhập. Đang thử lại...")
                                        list_count_error['login']+=1
                                        flag_closeFireFox=True
                                        break
                                    count_join_success+=1
                                    list_join_success.append(url)
                                    print(f"[{acc_name}] Đã tham gia vào URL: {url}.")
                        if count_join_success == len(list_url):
                            print(f"[{acc_name}] Đã tham gia vào tất cả các URL trong danh sách.")
                            break
                        else:
                            print(f"[{acc_name}] Không thể tham gia vào tất cả các URL trong danh sách. Đang thử lại...")
                            flag_closeFireFox=True
                            break
                            
                    print("đang chờ 1s")
                    time.sleep(0.5)

                
        except Exception as e:
            print(f"[{acc_name}] Lỗi: {e}")
            text_error+=f"[{acc_name}] Lỗi: {e}\n"
            flag_closeFireFox=True
            driver.save_screenshot(f"{acc_name}_error.png")
            
        if flag_closeFireFox==True:
            restart_count+=1
            # Đóng tất cả các tab trước khi quit
            try:
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.close()
            except Exception as e:
                print(f"Lỗi khi đóng tab: {e}")
            try:
                driver.quit()
            except Exception as e:
                print(f"Lỗi khi quit driver: {e}")
            continue
        else:
            # Xóa proxy khỏi profile sau khi chạy xong
            remove_proxy_from_profile(profile_path)
            try:
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.close()
            except Exception as e:
                print(f"Lỗi khi đóng tab: {e}")
            try:
                driver.quit()
            except Exception as e:
                print(f"Lỗi khi quit driver: {e}")
            return True
    if restart_count>=restart_max:
        if len(list_url)>len(list_join_success):
            for list in list_url:
                if list in list_join_success:continue
                else:
                    text_error+=f"[{acc_name}] Không thể tham gia vào URL: {list}. Đang thử lại...\n"
        count_error=0
        text_error2=""
        for  list_error in list_count_error:
            if list_count_error[list_error]>=3 and list_error !='wait_for_any_xpath_or_url':
                if list_error == "sign_in_hotmail":
                    text_error+=f"[{acc_name}] Không thể đăng nhập vào Hotmail. Đang thử lại...\n"
                elif list_error == "click_latest_password_reset_email":
                    text_error+=f"[{acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...\n"
                elif list_error == "edit_sheet_password_discord":
                    text_error+=f"[{acc_name}] Không thể cập nhật mật khẩu trong Google Sheets. Đang thử lại...\n"
                elif list_error == "login":
                    text_error+=f"[{acc_name}] Không thể đăng nhập. Đang thử lại...\n"
                elif list_error == "input_2fa":
                    text_error+=f"[{acc_name}] Không thể nhập mã 2FA. Đang thử lại...\n"
                elif list_error == "logic_resset_password":
                    text_error+=f"[{acc_name}] Không thể reset password. Đang thử lại...\n"
                count_error+=1
            if list_count_error[list_error]>0:
                if list_error == "sign_in_hotmail":
                    text_error2+=f"[{acc_name}] Không thể đăng nhập vào Hotmail. Đang thử lại...\n"
                elif list_error == "click_latest_password_reset_email":
                    text_error2+=f"[{acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...\n"
                elif list_error == "edit_sheet_password_discord":
                    text_error2+=f"[{acc_name}] Không thể cập nhật mật khẩu trong Google Sheets. Đang thử lại...\n"
                elif list_error == "login":
                    text_error2+=f"[{acc_name}] Không thể đăng nhập. Đang thử lại...\n"
                elif list_error == "input_2fa":
                    text_error2+=f"[{acc_name}] Không thể nhập mã 2FA. Đang thử lại...\n"
                elif list_error == "logic_resset_password":
                    text_error2+=f"[{acc_name}] Không thể reset password. Đang thử lại...\n"
                elif list_error == "wait_for_any_xpath_or_url":
                    text_error2+=f"[{acc_name}] Không thể tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Đang thử lại...\n"
                
        if count_error==0:
            text_error+=text_error2  
        write_error_to_file(log_file[0],log_file[1],acc_name,text_error)      
        return False
    return "Close"

# # Tạo và chạy các thread cho mỗi tài khoản
# threads = []
# accounts = {
#     "acc1": ("D:/profile_new/ACC (1)/Data/profile", "https://discord.com/login", (0, 0), (500, 500), "D:/drivers/acc1/geckodriver.exe", r"D:\profile_new\ACC (1)\App\firefox64\firefox.exe"),
#     "acc2": ("D:/profile_new/ACC (2)/Data/profile", "https://discord.com/login", (510, 0), (500, 500), "D:/drivers/acc2/geckodriver.exe", r"D:\profile_new\ACC (2)\App\firefox64\firefox.exe"),
# }

# for acc, (profile, url, position, size, geckopath, binary_location) in accounts.items():
#     t = threading.Thread(target=interact_discord, args=(profile, url, acc, position, size, geckopath, binary_location))
#     threads.append(t)
#     t.start()

# for t in threads:
#     t.join()

# print("✅ Tất cả acc đã mở và gửi nhiệm vụ xong!")






def set_zoom(driver, zoom_percent):
    # Dùng transform: scale cho Firefox
    scale = zoom_percent / 100.0
    js = f"document.body.style.transform='scale({scale})'; document.body.style.transformOrigin='0 0';"
    driver.execute_script(js)


def  stt_Acc(name_profile):
    match = re.search(r'ACC \((\d+)\)', name_profile)
    if not match:
        return False
    return int(match.group(1))

#Xử lý execl
def read_excel_file(filepath, sheet_name=None):
    """
    Đọc file Excel và trả về dữ liệu dạng list các tuple (row_index, row_data).
    - filepath: đường dẫn file excel
    - sheet_name: tên sheet muốn đọc (nếu None sẽ lấy sheet đầu tiên)
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        data = df.values.tolist()
        # Trả về list các tuple (row_index, row_data)
        data_with_index = [(idx+1, row) for idx, row in enumerate(data)]
        return data_with_index
    except Exception as e:
        print(f"Lỗi khi đọc file Excel: {e}")
        return None
def extract_first_integer(s):
    """
    Trả về dãy số nguyên đầu tiên trong chuỗi s (không bắt đầu bằng 0, trừ khi là '0').
    Nếu không tìm thấy, trả về None.
    """
    s=str(s)
    i = 0
    n = len(s)
    while i < n:
        if s[i].isdigit():
            # Nếu là số 0 đứng đầu và phía sau còn số, bỏ qua
            if s[i] == '0' and i+1 < n and s[i+1].isdigit():
                i += 1
                continue
            start = i
            while i < n and s[i].isdigit():
                i += 1
            return int(s[start:i])
        i += 1
    return None

def isLoad(driver, xpath=None, timeout=10):
    # Đợi document.readyState
    try:
        while True:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                break
            time.sleep(0.2)

        # Đợi network thực sự idle
        time.sleep(2)  # hoặc kiểm tra performance.timing như dưới

        load_end = driver.execute_script("return window.performance.timing.loadEventEnd")
        while load_end == 0 and not STOP_ALL_LOOPS:
            time.sleep(0.2)
            load_end = driver.execute_script("return window.performance.timing.loadEventEnd")
        print("Đã load xong trang.")
        print(f"Load time: {load_end - driver.execute_script('return window.performance.timing.navigationStart')} ms")
    except Exception as e:
        print(f"Lỗi khi kiểm tra trạng thái tải trang: {e}")
        return False
    return True
    


def process_excel_data(filepath, sheet_name=None):
    """
    Đọc file Excel và trả về list các tuple (row_index, num) với điều kiện cột Z là None.
    - filepath: đường dẫn file excel
    - sheet_name: tên sheet muốn đọc (nếu None sẽ lấy sheet đầu tiên)
    """
    profile_notOk = []
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        # Nếu df là dict (nhiều sheet), lấy sheet đầu tiên
        if isinstance(df, dict):
            first_sheet = list(df.keys())[0]
            df = df[first_sheet]
        for idx, row in enumerate(df.values.tolist()):
            if len(row) > 25:
                col_a = str(row[0]) if row[0] is not None else ""
                col_z = row[25]
                if pd.isna(col_z):
                    num = extract_first_integer(col_a)
                    if num is not None:
                        profile_notOk.append((idx, num))
    except Exception as e:
        print(f"Lỗi khi xử lý file Excel: {e}")
    return profile_notOk

# Ví dụ sử dụng:
# result = process_excel_data('duongdan.xlsx')
# print(result)

def write_error_to_file(path_file_error, sheet_name, profile_name, text_error):
    """
    Ghi dữ liệu lỗi vào sheet cụ thể trong file Excel.
    - Xóa hết dữ liệu cũ trong sheet đó trước khi ghi mới.
    - Cột A: profile_name, Cột B: text_error.
    """

    df = pd.DataFrame([[profile_name, text_error]])

    try:
        # Nếu file đã tồn tại, chỉ ghi đè sheet cần thiết, giữ nguyên các sheet khác
        with pd.ExcelWriter(path_file_error, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
    except FileNotFoundError:
        # Nếu file chưa tồn tại, tạo mới
        with pd.ExcelWriter(path_file_error, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
# write_error_to_file('Error_GPM - Copy.xlsx', 'Error', 'acc5', 'Không thể đăng nhập. Đang thử lại...')

def update_column_z_ok(path_data_excel, id_row):
    """
    Cập nhật 1 hoặc nhiều dòng (theo index) cột Z thành 'OK' trong file Excel.
    - id_row: int hoặc list[int] (index dòng, bắt đầu từ 0)
    """
    with excel_write_lock:
        try:
            df = pd.read_excel(path_data_excel)
            # Ép kiểu cột Z về object để gán giá trị không phải số
            df[df.columns[25]] = df[df.columns[25]].astype(object)
            if isinstance(id_row, list):
                for row in id_row:
                    if 0 <= row < len(df):
                        df.at[row, df.columns[25]] = "OK"
                print(f"Đã cập nhật các dòng {[r+1 for r in id_row]} cột Z thành 'OK' trong file {path_data_excel}")
            else:
                if 0 <= id_row < len(df):
                    df.at[id_row, df.columns[25]] = "OK"
                    print(f"Đã cập nhật dòng {id_row+1} cột Z thành 'OK' trong file {path_data_excel}")
            df.to_excel(path_data_excel, index=False)
        except Exception as e:
            print(f"Lỗi khi cập nhật file Excel: {e}")


# Ví dụ sử dụng:
# update_column_z_ok("duongdan.xlsx", 5)  # Sửa dòng thứ 6 (nếu id_row=5)

# Ví dụ sử dụng:
# data_excel = read_excel_file('duongdan.xlsx', sheet_name='Sheet1')
# process_excel_data(data_excel)
# print(profile_notOk)


# Ví dụ sử dụng:
# data = read_excel_file('duongdan.xlsx', sheet_name='Sheet1')
# print(data)
                    
                    