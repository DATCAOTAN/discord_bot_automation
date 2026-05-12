#Loogic reset password
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait     
from selenium.webdriver.support import expected_conditions as EC
from hotmail import sign_in_hotmail, click_latest_password_reset_email
from ggSheet import edit_sheet_password_discord
from main_fuction import check_captcha, set_zoom, click_or_mess_xpath, wait_for_any_xpath_or_url,input_2fa
import time
def logic_resset_password(driver, acc_name, email, password_hotmail, new_password_discord, secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID,zoom_body=100, list_count_error=None,stop_event=None):
        print(f"[{acc_name}] Đang bị reset password.")
        try:
            # Chờ và nhấn vào nút "Forgot your password?"
                # Đợi 1 giây trước khi tìm nút
            
            time_reset=0  # Lấy thời gian bắt đầu
            while  stop_event is not None and not stop_event.is_set() and True and time_reset<2 and not driver.find_elements(By.XPATH,  '//button[@type="submit" and .//div[text()="Okay"]]'):
                if wait_for_any_xpath_or_url(driver,['//button[@type="button" and .//div[text()="Forgot your password?"]]'],acc_name,zoom_body=zoom_body,stop_event=stop_event)==None:
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
                if check_captcha(driver,acc_name,['//button[@type="submit" and .//div[text()="Okay"]]'],zoom_body=zoom_body,stop_event=stop_event)== False:
                    print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
                    return False

                # Chờ nút "Okay" xuất hiện
                print(f"[{acc_name}] Đang chờ nút 'Okay' xuất hiện...")
                if(wait_for_any_xpath_or_url(driver,['//button[@type="submit" and .//div[text()="Okay"]]'],acc_name,zoom_body=zoom_body,stop_event=stop_event)):
                    print(f"[{acc_name}] Đã tìm thấy nút 'Okay'.")
                    break  # Thoát khỏi vòng lặp khi tìm thấy nút
                driver.refresh()
                set_zoom(driver, zoom_body)
                time_reset+=1
               
                # Nhấn nút "Okay"
            if click_or_mess_xpath(driver,acc_name,'//button[@type="submit" and .//div[text()="Okay"]]',mode="click",zoom_body=zoom_body,stop_event=stop_event)== False:
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
                if click_latest_password_reset_email(driver, acc_name,new_password_discord,secret_2fa,zoom_body=zoom_body,stop_event=stop_event)== False:
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

                    if sign_in_hotmail(driver, email, password_hotmail,acc_name,zoom_body=zoom_body,stop_event=stop_event)== False:
                        print(f"[{acc_name}] Không thể đăng nhập vào Hotmail. Đang thử lại...")
                        list_count_error['sign_in_hotmail']+=1
                        return False
                    print(f"[{acc_name}] Đã thực hiện đăng nhập vào Hotmail.")
                    time.sleep(1)
                    driver.get("https://outlook.live.com/mail/0/")
                    set_zoom(driver, zoom_body)
                    time.sleep(1)
                    print(f"[{acc_name}] Đã chuyển hướng thành công đến Hotmail.")
                    if click_latest_password_reset_email(driver, acc_name,new_password_discord,secret_2fa,zoom_body=zoom_body,stop_event=stop_event)== False:
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
def logic_login_and_reset_password_discord(driver, acc_name,wait,email,password_discord,password_hotmail,new_password_discord,secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID,zoom_body=100, list_count_error=None,stop_event=None):
            while  stop_event is not None and not stop_event.is_set() and not driver.find_elements(By.XPATH, '//input[@placeholder="6-digit authentication code"]') and not driver.find_elements(By.XPATH, "//label[contains(text(), 'Email or Phone Number') and .//span[.//span]]") and not driver.find_elements(By.XPATH, "//div[contains(text(), 'Find or start a conversation')]"):
                print(f"[{acc_name}] Đang chờ trang Discord load xong...")
                if(wait_for_any_xpath_or_url(driver, ['//button[@type="button" and .//div[text()="Log in"]]', '//button[@type="submit" and .//div[text()="Log In"]]'], 130, 0.5,zoom_body=zoom_body,stop_event=stop_event)==None):           
                    print(f"[{acc_name}] Không tìm thấy nút 'Log in' hoặc 'Log In'. Đang thử lại...")
                    list_count_error['wait_for_any_xpath_or_url']+=1
                    return False
                print(f"[{acc_name}] Đã tìm thấy nút 'Log in' hoặc 'Log In'.")
                if(driver.find_elements(By.XPATH, '//button[@type="button" and .//div[text()="Log in"]]')):
                    print(f"[{acc_name}] Đã tìm thấy nút 'Log in' loai button.")
                    element=driver.find_element(By.XPATH, '//button[@type="button" and .//div[text()="Log in"]]')
                    try:
                        element.click()
                    except:
                        print(f"[{acc_name}] Lỗi khi click vào nút 'Log in'.")
                        continue

                print(f"[{acc_name}] Đã tìm thấy nút 'Log In'.")
                login_button =  wait.until(EC.presence_of_element_located((By.XPATH,  '//button[@type="submit" and .//div[text()="Log In"]]')))
                print(f"[{acc_name}] Chưa đăng nhập. Đang thực hiện đăng nhập...")
                email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
                password_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
                email_input.send_keys(email)
                password_input.send_keys(password_discord)
                try:
                    login_button.click()
                except:
                    print(f"[{acc_name}] Lỗi khi click vào nút 'Log In'.")
                    continue
                if check_captcha(driver,acc_name,['//input[@placeholder="6-digit authentication code"]',"//label[contains(text(), 'Email or Phone Number') and .//span[.//span]]","//div[contains(text(), 'Find or start a conversation')]"],zoom_body=zoom_body,stop_event=stop_event) == False:
                    print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
                    return False
                time.sleep(2)
            # Kiểm tra xem có yêu cầu nhập mã 2FA không
            if driver.current_url == "https://discord.com/channels/@me":
                    print(f"[{acc_name}] Đã đăng nhập mà không cần mã 2FA.")
                    return True
            else:
                if driver.find_elements(By.XPATH, "//label[contains(text(), 'Email or Phone Number') and .//span[.//span]]"):
                        if logic_resset_password(driver, acc_name, email, password_hotmail, new_password_discord, secret_2fa,sheet_name, row,SERVICE_ACCOUNT_FILE,SHEET_ID,zoom_body, list_count_error=list_count_error,stop_event=stop_event)== False:
                            print(f"[{acc_name}] Không thể reset password. ")
                            list_count_error['logic_resset_password']+=1
                            return False
                        else:
                            print(f"[{acc_name}] Đã reset password thành công.")
                            return True
            
            
                else:
                    if input_2fa(driver, acc_name, secret_2fa,list_count_error=list_count_error,zoom_body=zoom_body,stop_event=stop_event) == False:
                        print(f"[{acc_name}] Không thể nhập mã 2FA. Đang thử lại...")
                        list_count_error['input_2fa']+=1
                        return False
                    else:
                        return True
#Join discord
def logic_join_url_discord(driver, acc_name, url, load_max=3,zoom_body=100, list_count_error=None,stop_event=None):
    count_load = 0
    while  stop_event is not None and not stop_event.is_set() and count_load < load_max:
        driver.get(url)
        set_zoom(driver, zoom_body)
        # Chờ nút Accept Invite xuất hiện
        if wait_for_any_xpath_or_url(driver, ["//button[.//div[text()='Accept Invite']]"], 130, 0.5,zoom_body=zoom_body,stop_event=stop_event) is None:
            list_count_error['wait_for_any_xpath_or_url']+=1
            print(f"[{acc_name}] Không tìm thấy nút 'Accept Invite'. Đang tải lại trang...")
            return False
        accept_invite_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='Accept Invite']]"))
        )
        accept_invite_button.click()
        if check_captcha(driver, acc_name,[
                "//button[.//div[contains(text(), 'Continue to Discord')]]",
            ], url="https://discord.com/channels",zoom_body=zoom_body,stop_event=stop_event) == False:
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
            130, 0.5, url="https://discord.com/channels",zoom_body=zoom_body,stop_event=stop_event
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
                if check_captcha(driver, acc_name,[
                        "//button[.//div[contains(text(), 'Continue to Discord')]]",
                    ],zoom_body=zoom_body,stop_event=stop_event) == False:
                    print(f"[{acc_name}] Không thể vượt qua captcha. Đang tải lại trang...")
                    return False
                time.sleep(6)
                if wait_for_any_xpath_or_url(
                    driver,
                    [
                        "//button[.//div[contains(text(), 'Continue to Discord')]]",
                        "//button[.//div[text()='Accept Invite']]"
                    ],
                    30, 0.5, url="https://discord.com/channels",zoom_body=zoom_body,stop_event=stop_event
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