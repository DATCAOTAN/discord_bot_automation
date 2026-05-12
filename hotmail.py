import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from main_fuction import click_or_mess_xpath, wait_for_any_xpath_or_url, set_zoom, isLoad, input_2fa,wait_find_element_and_load_and_delete_cookies
def sign_in_hotmail(driver, email, password,acc_name,zoom_body=100, list_count_error=None,stop_event=None):

    try:
        # Nhập email vào ô input
        # Tìm thẻ <a> có class="btn"
        time_start=0  # Lấy thời gian bắt đầu
        while  stop_event is not None and not stop_event.is_set() and True and time_start < 60:
            if not driver.find_elements(By.XPATH, '//input[@type="email" and @id="usernameEntry"]'):
                driver.get("https://login.live.com/")
                set_zoom(driver, zoom_body)
                time_start+=5

                time.sleep(5)  # Chờ 1 giây trước khi kiểm tra lại
            else:
                print(f"[{acc_name}] Đã tìm thấy thẻ ")
                break
        if stop_event.is_set():
            return False
        time_start=0
        while  stop_event is not None and not stop_event.is_set() and not driver.find_elements(By.XPATH, '//input[ @type="password" and @id="passwordEntry" ] ') and time_start<60:
            if click_or_mess_xpath(driver,acc_name,'//input[@type="email" and @id="usernameEntry"]',mode="mess",mess=email,x_path_success='//input[@type="email" and @id="usernameEntry" and @value="'+email+'"]',zoom_body=zoom_body,stop_event=stop_event) == False:
                print(f"[{acc_name}] Không thể tìm thấy ô nhập email. Đang tải lại trang...")
                list_count_error['sign_in_hotmail']+=1
                return False
            print(f"[{acc_name}] Đã nhập email: {email}")
            # Nhấn nút "Next"
            if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and @data-testid="primaryButton"]',mode="click",zoom_body=zoom_body,stop_event=stop_event)==False:
                print(f"[{acc_name}] Không thể tìm thấy nút 'Next'. Đang tải lại trang...")
                list_count_error['sign_in_hotmail']+=1
                return False
            time.sleep(3)  # Chờ 1 giây trước khi kiểm tra lại  
            print(f"[{acc_name}] Đã nhấn nút 'Next'.")
            time_start+=3
        if stop_event.is_set():
            return False
        

        # Nhập mật khẩu vào ô input
        password_input = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//input[ @type="password" and @id="passwordEntry" ] '))
        )
        password_input.send_keys(password)
        print(f"[{acc_name}] Đã nhập mật khẩu.")

        if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and @data-testid="primaryButton"]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy nút 'Next'. Đang tải lại trang...")
            return False

        next_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @data-testid="primaryButton"]'))
        )
        next_button.click()
        print(f"[{acc_name}] Đã nhấn nút 'Next'.")
        if wait_for_any_xpath_or_url(driver,['//button[@type="submit" and @data-testid="primaryButton"]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
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
def click_latest_password_reset_email(driver, acc_name, new_password, secret_2fa,list_count_error=None,zoom_body=100,stop_event=None):
    count_restart=0
    if wait_find_element_and_load_and_delete_cookies(driver,'//input[@placeholder="Search"]',acc_name,zoom_body=zoom_body,stop_event=stop_event) == False:
        print(f"[{acc_name}] chưa load xong trang hotmail.")
        list_count_error['click_latest_password_reset_email']+=1
        return False
    if( driver.find_elements(By.XPATH, '//span[contains(@class, "ms-Pivot-text") and text()="Other"]')):
        print(f"[{acc_name}] Đã tìm thấy thẻ <span> có class 'ms-Pivot-text' và text 'Other'.")
        isLoad(driver,zoom_body=zoom_body,stop_event=stop_event)
        if click_or_mess_xpath(driver,acc_name,'//span[contains(@class, "ms-Pivot-text") and text()="Other"]',mode="click",x_path_success='//span[contains(text(), "Password Reset Request for Discord")]',load_page=30,zoom_body=zoom_body,stop_event=stop_event)==False:
            print(f"[{acc_name}] Không thể click vào nút 'Other'. Đang tải lại trang...")
            list_count_error['click_latest_password_reset_email']+=1
            return False
    try:
        
    
        # Click vào email

        while  stop_event is not None and not stop_event.is_set() and True and count_restart<3:
            if wait_for_any_xpath_or_url(driver,['//span[contains(text(), "Password Reset Request for Discord")]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
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
            flag_click=False
            count_click=0
            while  stop_event is not None and not stop_event.is_set() and True and flag_click==False and count_click<20:
                try:
                    latest_email.click()
                    flag_click=True
                    break  # Thoát khỏi vòng lặp nếu click thành công
                except Exception as e:
                    print(f"[{acc_name}] Lỗi khi click vào email: {e}. Đang thử lại...")
                    time.sleep(1)
                    count_click+=1
            if flag_click==False:
                count_restart+=1
                driver.refresh()
                set_zoom(driver, zoom_body)
            else:
                break
        if stop_event.is_set():
            return False
        print(f"[{acc_name}] Đã click vào email gần đây nhất.")

        if wait_for_any_xpath_or_url(driver,['//a[contains(text(), "Reset Password")]'],130,0.5,zoom_body=zoom_body,stop_event=stop_event)==None:
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
        while  stop_event is not None and not stop_event.is_set() and not driver.find_elements(By.XPATH, '//input[@placeholder="6-digit authentication code"]')and time_start<4:
            if click_or_mess_xpath(driver,acc_name,'//input[@type="password" and @name="password"]',mode="mess",mess=new_password,x_path_success=f'//input[@type="password" and @name="password" and @value="{new_password}"]',zoom_body=zoom_body,stop_event=stop_event)==False:
                print(f"[{acc_name}] Không thể tìm thấy ô nhập mật khẩu mới. Đang tải lại trang...")
                list_count_error['click_latest_password_reset_email']+=1
                continue
            print(f"[{acc_name}] Đã nhập mật khẩu mới: {new_password}")

            # Click vào nút "Change Password"
            
            if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and .//div[text()="Change Password"]]',zoom_body=zoom_body,stop_event=stop_event):
                print(f"[{acc_name}] Đã click vào nút 'Change Password'.")
            else:
                print(f"[{acc_name}] Không thể click vào nút 'Change Password'. Đang tải lại trang...")
                list_count_error['click_latest_password_reset_email']+=1
                continue
            time.sleep(2)
            if driver.find_elements(By.XPATH, '//button[@type="submit" and .//div[text()="Change Password"]]'):
                if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and .//div[text()="Change Password"]]',zoom_body=zoom_body,stop_event=stop_event):
                    print(f"[{acc_name}] Đã click vào nút 'Change Password'.")
                else:
                    print(f"[{acc_name}] Không thể click vào nút 'Change Password'. Đang tải lại trang...")
                    list_count_error['click_latest_password_reset_email']+=1
                    continue
            else:
                print(f"[{acc_name}] Đã click vào nút 'Change Password'.")
                break
            time.sleep(1)
            time_start+=1
        if stop_event.is_set():
            return False
        print(f"[{acc_name}] Đã nhập mật khẩu mới và click vào nút 'Change Password'.")
        if input_2fa(driver,acc_name,secret_2fa,zoom_body=zoom_body,stop_event=stop_event)== False:
            print(f"[{acc_name}] Không thể nhập mã 2FA. Đang tải lại trang...")
            list_count_error['input_2fa']+=1
            return False
        return True
    except Exception as e:
        print(f"[{acc_name}] Lỗi khi xử lý email hoặc đổi mật khẩu: {e}")
        return False