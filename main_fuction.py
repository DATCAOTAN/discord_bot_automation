import time
import os
import re
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import requests
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
def isLoad(driver, xpath=None, timeout=10,stop_event=None,zoom_body=100):
    # Đợi document.readyState
    try:
        while  stop_event is not None and  not stop_event.is_set() and   True:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                break
            time.sleep(0.2)
        if stop_event.is_set():
            return False

        # Đợi network thực sự idle
        time.sleep(2)  # hoặc kiểm tra performance.timing như dưới

        load_end = driver.execute_script("return window.performance.timing.loadEventEnd")
        while  stop_event is not None and  not stop_event.is_set() and   load_end == 0:
            print(f"Load time: {load_end - driver.execute_script('return window.performance.timing.navigationStart')} ms")
            print(f"stop_event: {stop_event.is_set()}")
            print("Đang chờ load trang : ")
            load_end = driver.execute_script("return window.performance.timing.loadEventEnd")
        print("Đã load xong trang.")
        print(f"Load time: {load_end - driver.execute_script('return window.performance.timing.navigationStart')} ms")
        if stop_event.is_set():
            return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra trạng thái tải trang: {e}")
        return False
    return True
def wait_for_any_xpath_or_url(driver, xpath_list, timeout=130, poll_frequency=0,url=None,reload_time=60, zoom_body=100,stop_event=None):
    """
    Chờ cho đến khi ít nhất 1 trong các xpath trong mảng xuất hiện trên trang (hoặc hết timeout).
    Nếu sau 10s chưa thấy thì reload lại trang.
    Trả về xpath nào xuất hiện đầu tiên, hoặc None nếu hết timeout.
    """
    time_start=0
    end_time = time_start + 130
    reload = reload_time  # Sau 10s sẽ rel
    while  stop_event is not None and  not stop_event.is_set() and   True and time_start<end_time:
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

def set_zoom(driver, zoom_percent):
    browser_name = driver.capabilities.get('browserName', '').lower()
    print(f"browser_name: {browser_name}")
    scale = zoom_percent / 100.0

    if 'firefox' in browser_name:
        # Firefox: scale và chỉnh lại width/height cho body
        driver.execute_script(
            f"""
            document.body.style.transform = 'scale({scale})';
            document.body.style.transformOrigin = '0 0';
            document.body.style.width = '{100/scale}%';
            document.body.style.height = '{100/scale}%';
            """
        )
    else:
        # Chrome, Edge, Opera: dùng zoom
        driver.execute_script(f"document.body.style.zoom = '{zoom_percent}%';")


def  stt_Acc(name_profile, zoom_body=100):
    match = re.search(r'ACC \((\d+)\)', name_profile)
    if not match:
        return False
    return int(match.group(1))
def click_or_mess_xpath(driver,acc_name,xpath,mode="click",mess="",x_path_success=None,count_restarmax=5,load_page=0,stop_event=None,zoom_body=100):
    count_restar=0
    count=0
    load=load_page
    print(f"[{acc_name}] Đang tìm phần tử với XPath: {xpath} và mode: {mode}")
    print(f'[{acc_name}] mess: {mess} success_xpath: {x_path_success}')
    while  stop_event is not None and  not stop_event.is_set() and   True and count<count_restarmax:
        if wait_for_any_xpath_or_url(driver,[xpath],zoom_body=zoom_body,stop_event=stop_event)==None:
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
                element.click()
                print(f"[{acc_name}] Đã click vào phần tử với XPath: {xpath} để nhập văn bản.")
                element.send_keys(Keys.CONTROL, 'a')
                element.send_keys(mess)
                print(f"[{acc_name}] Đã nhập văn bản: {mess}")
                print(f"[{acc_name}] Đã tìm thấy phần tử với XPath: {xpath}")
            
            if x_path_success is not None:
                if isLoad(driver,stop_event=stop_event,zoom_body=zoom_body)==False:
                    return False
                if driver.find_elements(By.XPATH, x_path_success) :
                    print(f"[{acc_name}] Đã tìm thấy phần tử với XPath thành công: {x_path_success}.")
                    return True
                print(f"[{acc_name}] Không tìm thấy phần tử với XPath thành công: {x_path_success}. Đang tải lại trang...")
                driver.refresh()  # Tải lại trang hiện tại
                set_zoom(driver, zoom_body)
            return True  # Click hoặc nhập văn bản thành công
        except Exception as e:
            count_restar+=1
            if count_restar>load:
                print(f"[{acc_name}] Đã thử {count_restar} lần mà không tìm thấy phần tử với XPath: {xpath}. Đang tải lại trang...")
                driver.refresh()
                set_zoom(driver, zoom_body)
                count+=1
                count_restar=0  # Đặt lại thời gian bắt đầu
            print(f"[{acc_name}] Lỗi khi click hoặc tìm phần tử với XPath: {xpath}. Lỗi: {e}")
    return False  # Không tìm thấy phần tử sau 60 giây
#Hàm kiểm tra captcha đã vượt hay chưa            
def check_captcha(driver,acc_name,Listxpath_noCaptcha=None,url=None,stop_event=None,zoom_body=100):
    time_start = 0  # Lấy thời gian bắt đầu
    while  stop_event is not None and  not stop_event.is_set() and   True and  time_start < 100:
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
    if stop_event.is_set():
        return False
    time_start=0
    while  stop_event is not None and  not stop_event.is_set() and   True and  time_start < 100:
            captcha_element = driver.find_elements(By.XPATH, '//div[contains(text(), "Wait! Are you human?")]')
            if not captcha_element:
                print(f"[{acc_name}] Captcha đã biến mất. Tiếp tục thực hiện.")
                return True  # Thoát khỏi vòng lặp khi captcha không còn
            else:
                print(f"[{acc_name}] Đang chờ captcha biến mất...")
                time.sleep(1)  # Chờ 1 giây trước khi kiểm tra lại
                time_start+=1
    return False  # Nếu đã chờ quá thời gian quy định mà vẫn không biến mất, trả về False
#Kiểm tra xem có thể tìm thấy xpath hay không và load trang và xoá cookies
def wait_find_element_and_load_and_delete_cookies(driver, xpath, acc_name,zoom_body=100,stop_event=None):
        start_time = 0  # Lấy thời gian bắt đầu
        count = 0  # Biến đếm số lần thử
        count_delete_cookies = 0  # Biến đếm số lần xóa cookies 
        while  stop_event is not None and  not stop_event.is_set() and   True and count_delete_cookies<2:
            if wait_for_any_xpath_or_url(driver,['//input[@placeholder="6-digit authentication code"]','//span[contains(@class, "ms-Pivot-text") and text()="Other"]',
                                                 '//span[contains(text(), "Password Reset Request for Discord")]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
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
def input_2fa(driver,acc_name,secret_2fa,list_count_error=None,stop_event=None,zoom_body=100):
    try:
        if wait_for_any_xpath_or_url(driver,['//input[@placeholder="6-digit authentication code"]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy ô nhập mã 2FA. Đang tải lại trang...")
            return False  # Không tìm thấy ô nhập mã 2FA
        
        two_fa_input= WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="6-digit authentication code"]')))
        print(f"[{acc_name}] Yêu cầu nhập mã 2FA. Đang lấy mã...")
        token = get_2fa_token(secret_2fa, zoom_body)
        if token:
            two_fa_input.send_keys(token)
            try:
                if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and .//div[text()="Confirm"]]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
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
    # Hàm lấy mã 2FA từ trang web
def get_2fa_token(secret_key, zoom_body=100):
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
#Kiểm tra xem có thể tìm thấy xpath hay không và load trang và xoá cookies
