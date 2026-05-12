from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
import time
from selenium.webdriver.common.keys import Keys
from excel import  write_error_to_file
from ggSheet import get_sheet_and_row, read_google_sheet
from logic_discord import  logic_login_and_reset_password_discord,logic_join_url_discord
from main_fuction import remove_proxy_from_profile, set_zoom, isLoad, click_or_mess_xpath, wait_for_any_xpath_or_url
from threading import Event
class DiscordBot:
    def __init__(self, profile_path: str, url:str, acc_name: str, position:tuple, size:tuple, geckopath:str, binary_location:str, mission_text:str, proxy=None, SERVICE_ACCOUNT_FILE=None, SHEET_ID=None, sheet_name=None,
                  zoom=100, size_goc=None, thread_index=0, restart_max=1000, list_url=None, log_file=None, mode="manual", stop_event=Event(),captcha=False,captcha_ext_url=None):
        self.profile_path = profile_path
        self.url = url
        self.acc_name = acc_name
        self.sheet_name = sheet_name
        self.SERVICE_ACCOUNT_FILE = SERVICE_ACCOUNT_FILE
        self.SHEET_ID = SHEET_ID
        self.position = position
        self.size = size    
        self.geckopath = geckopath
        self.binary_location = binary_location
        self.mission_text = mission_text
        self.proxy = proxy
        self.zoom = zoom
        self.size_goc = size_goc
        self.thread_index = thread_index
        self.restart_max = restart_max
        self.list_url = list_url if list_url is not None else []
        self.log_file = log_file if log_file is not None else []
        self.mode = mode
        self.captcha = captcha
        self.list_count_error = {
            'get_sheet_and_row': 0,
            'read_google_sheet': 0,
            'sign_in_hotmail': 0,
            'click_latest_password_reset_email': 0,
            'edit_sheet_password_discord': 0,
            'login': 0,
            'input_2fa': 0,
            'logic_resset_password': 0,
            'wait_for_any_xpath_or_url': 0,
            'click_find': 0,
            'click_quick_switcher': 0,
            'click_ApeApefan': 0
        }
        self.list_join_success = []
        self.nhiem_vu = {
            'Find or start a conversation': False,
            'ApeApefan': False,
            'click_ApeApefan': False,
            'Gửi nhiệm vụ': False,
            'Hoàn thành': False,
            'dang_nhap': False
        }
        self.text_error = ""
        self.restart_count = 0
        self.zoom_body = zoom
        self.flag_close=False
        self.stop_event=stop_event
        self.captcha_ext_url = captcha_ext_url
    def stop(self):
        self.stop_event.set()

    def run(self):
        self.restart_count = 0
        self.zoom_body = self.zoom
        self.list_join_success = []
        self.nhiem_vu = {
            'Find or start a conversation': False,
            'ApeApefan': False,
            'click_ApeApefan': False,
            'Gửi nhiệm vụ': False,
            'Hoàn thành': False,
            'dang_nhap': False
        }
        self.text_error = ""
        driver=None
        while self.stop_event is not None and  not self.stop_event.is_set() and True and self.restart_count < self.restart_max:
            flag_closeFireFox = False
            self.nhiem_vu['dang_nhap'] = False
            self.row = get_sheet_and_row(self.profile_path)
            if self.sheet_name is None:
                print(f"[{self.acc_name}] Không thể lấy tên sheet và hàng từ profile. Đang thử lại...")
                self.list_count_error['get_sheet_and_row'] += 1
                self.text_error = "Không thể lấy tên sheet và hàng từ profile."
                write_error_to_file(self.log_file[0], self.log_file[1], self.acc_name, self.text_error)
                return False
            self.account_data = read_google_sheet(self.sheet_name, self.row, self.SERVICE_ACCOUNT_FILE, self.SHEET_ID)
            if self.account_data == False:
                print(f"[{self.acc_name}] Không thể đọc dữ liệu từ Google Sheets. Đang thử lại...")
                self.list_count_error['read_google_sheet'] += 1
                self.text_error = "Không thể đọc dữ liệu từ Google Sheets."
                write_error_to_file(self.log_file[0], self.log_file[1], self.acc_name, self.text_error)
                return False
            remove_proxy_from_profile(self.profile_path)
            try:
                print(f"[{self.acc_name}] Opening Discord)")
                options = Options()
                options.binary_location = self.binary_location
                options.add_argument("-profile")
                options.add_argument(self.profile_path)
                options.set_preference("browser.startup.homepage_override.mstone", "ignore")
                options.set_preference("startup.homepage_welcome_url.additional", "about:blank")
                options.set_preference("dom.webdriver.enabled", False)
                options.set_preference("useAutomationExtension", False)
                if self.proxy:
                    host, port = self.proxy.split(":", 1)
                    print(f"[{self.acc_name}] Dùng proxy HTTP/HTTPS: {host}:{port}")
                    options.set_preference("network.proxy.type", 1)
                    options.set_preference("network.proxy.http", host)
                    options.set_preference("network.proxy.http_port", int(port))
                    options.set_preference("network.proxy.ssl", host)
                    options.set_preference("network.proxy.ssl_port", int(port))
                    options.set_preference("network.proxy.no_proxies_on", "")
                else:
                    print(f"[{self.acc_name}] Sử dụng proxy hệ thống.")
                service = Service(executable_path=self.geckopath)
                driver = webdriver.Firefox(service=service, options=options)
                if self.size:
                    driver.set_window_size(self.size[0], self.size[1])
                    print(f"[{self.acc_name}] Kích thước cửa sổ: {driver.get_window_size()}")
                if self.position:
                    driver.set_window_position(self.position[0], self.position[1])
                    print(f"[{self.acc_name}] Vị trí cửa sổ: ({self.position[0]}, {self.position[1]})")
                driver.get(self.captcha_ext_url)
                isLoad(driver,stop_event=self.stop_event)
                element = driver.find_element(By.XPATH, "//input[ @type='checkbox']")
                if self.captcha:
                    if(element.is_selected() == False):
                        print(f"[{self.acc_name}] chưa click captha đang click......")
                        element.click()
                    else: print(f"[{self.acc_name}] đã click captha")
                else:
                    if(element.is_selected() == True):
                        element.click()
                    else: print(f"[{self.acc_name}] đã tắt captcha")
                driver.get("https://discord.com/login")
                print(f"[{self.acc_name}] Đã mở Discord.")
                if isLoad(driver,stop_event=self.stop_event) == False:
                    flag_closeFireFox = True
                    print(f"[{self.acc_name}] Trang chưa load xong. Đang thử lại...")
                    self.list_count_error['isLoad'] += 1
                    self.text_error = "Trang chưa load xong."
                print("da load xong")
                set_zoom(driver, self.zoom_body)
                if wait_for_any_xpath_or_url(driver, ['//button[@type="submit" and .//div[text()="Log In"]]', 
                                                                  '//div[contains(text(), "Find or start a conversation")]', 
                                                                  '//button[@type="button" and .//div[text()="Log in"]]'], 130, 0.5,stop_event=self.stop_event) == None:
                    print(f"[{self.acc_name}] Không tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Restarting...")
                    self.list_count_error['wait_for_any_xpath_or_url'] += 1
                    continue
                wait = WebDriverWait(driver, 60)
                set_zoom(driver, self.zoom_body)
                while self.stop_event is not None and   not self.stop_event.is_set() and True and flag_closeFireFox == False:
                    try:
                        print(f"[{self.acc_name}] Trang đã load xong.")
                        self.email = self.account_data[1]
                        self.password_discord = self.account_data[2]
                        self.secret_2fa = self.account_data[3]
                        self.password_hotmail = self.account_data[4]
                        self.new_password_discord = self.password_discord + "a"
                        print(f"[{self.acc_name}] Sử dụng sheet: {self.sheet_name}, hàng: {self.row}")
                        print(f"[{self.acc_name}] Bắt đầu tương tác với Discord.")
                        current_tab = driver.current_window_handle
                        driver.switch_to.window(current_tab)
                        current_url = driver.current_url
                        if "about:preferences#moreFromMozilla" in current_url:
                            print(f"[{self.acc_name}] Đang thoát profile.")
                            print("Dừng kiểm tra và thoát.")
                            driver.quit()
                            return 1
                        elif "about:preferences#experimental" in current_url:
                            self.nhiem_vu['dang_nhap'] = False
                            driver.get("https://discord.com/login")
                            set_zoom(driver, self.zoom_body)
                            if wait_for_any_xpath_or_url(driver, ['//button[@type="submit" and .//div[text()="Log In"]]', 
                                                                  '//div[contains(text(), "Find or start a conversation")]', '//button[@type="button" and .//div[text()="Log in"]]'], 130, 0.5,stop_event=self.stop_event) == None:
                                print(f"[{self.acc_name}] Không tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Restarting...")
                                self.list_count_error['wait_for_any_xpath_or_url'] += 1
                                continue
                            if ("https://discord.com/login" not in driver.current_url):
                                print(f"[{self.acc_name}] Đã chuyển hướng đến URL: {driver.current_url}")
                                continue
                            if logic_login_and_reset_password_discord(driver, self.acc_name, wait, self.email, self.password_discord, self.password_hotmail, self.new_password_discord, self.secret_2fa, 
                                                                      self.sheet_name, self.row, self.SERVICE_ACCOUNT_FILE, self.SHEET_ID,stop_event=self.stop_event,list_count_error=self.list_count_error) == False:
                                print(f"[{self.acc_name}] Không thể đăng nhập. Đang thử lại...")
                                self.list_count_error['login'] += 1
                                flag_closeFireFox = True
                                break
                            self.nhiem_vu['dang_nhap'] = True
                        elif "about:preferences#sync" in current_url:
                            print(f"[{self.acc_name}] Đang thoát profile.")
                            print("Dừng kiểm tra và thoát.")
                            driver.quit()
                            return "close"
                        else:
                            print(f"[{self.acc_name}] Bỏ qua kiểm tra.")
                    except Exception as e:
                        print(f"[{self.acc_name}] Lỗi: {e}")
                        print("Tao cố ý")
                        flag_closeFireFox = True
                        break
                    if self.nhiem_vu['dang_nhap'] == False:
                        print("chuwa dang nhap")
                        print(driver.current_url)
                        if "https://discord.com/channels/@me" in driver.current_url:
                            self.nhiem_vu['dang_nhap'] = True
                            print(f"[{self.acc_name}] Đã chuyển hướng thành công đến Discord.")
                        elif self.nhiem_vu['dang_nhap'] == False and "https://discord.com/login" in driver.current_url:
                            if logic_login_and_reset_password_discord(driver, self.acc_name, wait, self.email, self.password_discord, self.password_hotmail, self.new_password_discord, self.secret_2fa, self.sheet_name,
                                                                       self.row, self.SERVICE_ACCOUNT_FILE, self.SHEET_ID,stop_event=self.stop_event,list_count_error=self.list_count_error) == False:
                                print(f"[{self.acc_name}] Không thể đăng nhập. Đang thử lại...")
                                self.list_count_error['login'] += 1
                                flag_closeFireFox = True
                                break
                            self.nhiem_vu['dang_nhap'] = True
                    else:
                        print("da dang nhap thanh cong")
                    while self.stop_event is not None and  not self.stop_event.is_set() and self.nhiem_vu['Hoàn thành'] == False and self.mode == "manual" and self.nhiem_vu['dang_nhap'] == True:
                        if self.nhiem_vu['Find or start a conversation'] == False:
                            try:
                                if click_or_mess_xpath(driver, self.acc_name, '//div[contains(text(), "Find or start a conversation")]', mode="click",load_page=15,stop_event=self.stop_event) == False:
                                    print(f"[{self.acc_name}] Không thể click vào nút 'Find or start a conversation'. Đang thử lại...")
                                    self.list_count_error['click_find'] += 1
                                    if (self.list_count_error['click_find'] > 10):
                                        print(f"[{self.acc_name}] Không thể click vào nút 'Find or start a conversation'. Đang thử lại...")
                                        self.list_count_error['click_find'] = 0
                                    continue
                                print(f"[{self.acc_name}] Đã click vào nút 'Find or start a conversation'.")
                                self.nhiem_vu['Find or start a conversation'] = True
                            except Exception as e:
                                print(f"[{self.acc_name}] Không tìm thấy nút 'Find or start a conversation'. Restarting... Error: {e}")
                                self.list_count_error['click_find'] += 1
                                if (self.list_count_error['click_find'] > 10):
                                    print(f"[{self.acc_name}] Không thể click vào nút 'Find or start a conversation'. Đang thử lại...")
                                    self.list_count_error['click_find'] = 0
                                continue
                        elif self.nhiem_vu['ApeApefan'] == False:
                            try:
                                if click_or_mess_xpath(driver, self.acc_name, '//input[@aria-label="Quick switcher"]', mode="mess", mess="ApeApefan",
                                                        x_path_success='//input[@aria-label="Quick switcher" and @value="ApeApefan"]',stop_event=self.stop_event) == False:
                                    print(f"[{self.acc_name}] Không thể click vào thanh tìm kiếm. Đang thử lại...")
                                    self.list_count_error['click_quick_switcher'] += 1
                                    if (self.list_count_error['click_quick_switcher'] > 10):
                                        print(f"[{self.acc_name}] Không thể click vào thanh tìm kiếm. Đang thử lại...")
                                        self.list_count_error['click_quick_switcher'] = 0
                                    continue
                                print(f"[{self.acc_name}] Đã click vào thanh tìm kiếm.")
                                self.nhiem_vu['ApeApefan'] = True
                                print(f"[{self.acc_name}] Đã nhập 'ApeApefan' vào thanh tìm kiếm.")
                            except Exception as e:
                                print(f"[{self.acc_name}] Không tìm thấy thanh tìm kiếm. Restarting... Error: {e}")
                                continue
                        elif self.nhiem_vu['click_ApeApefan'] == False:
                            try:
                                if click_or_mess_xpath(driver, self.acc_name, '(//div[@aria-label="ApeApefan, User, apeapefan"])[1]', mode="click",stop_event=self.stop_event) == False:
                                    print(f"[{self.acc_name}] Không thể click vào server đầu tiên. Đang thử lại...")
                                    self.list_count_error['click_ApeApefan'] += 1
                                    if (self.list_count_error['click_ApeApefan'] > 10):
                                        print(f"[{self.acc_name}] Không thể click vào server đầu tiên. Đang thử lại...")
                                        self.list_count_error['click_ApeApefan'] = 0
                                    continue
                                self.nhiem_vu['click_ApeApefan'] = True
                                print(f"[{self.acc_name}] Đã tìm thấy và click vào server đầu tiên.")
                            except Exception as e:
                                print(f"[{self.acc_name}] Không tìm thấy server đầu tiên. Restarting... Error: {e}")
                                continue
                        elif self.nhiem_vu['Gửi nhiệm vụ'] == False:
                            try:
                                if wait_for_any_xpath_or_url(driver, ['//div[@role="textbox" and @contenteditable="true"]'], 130, 0.5,stop_event=self.stop_event) == None:
                                    print(f"[{self.acc_name}] Không tìm thấy ô chat. Restarting...")
                                    self.list_count_error['wait_for_any_xpath_or_url'] += 1
                                    flag_closeFireFox = True
                                    break
                                message_box = wait.until(EC.presence_of_element_located((
                                    By.XPATH, '//div[@role="textbox" and @contenteditable="true"]'
                                )))
                                message_box.send_keys(self.mission_text)
                                message_box.send_keys(Keys.ENTER)
                                self.nhiem_vu['Gửi nhiệm vụ'] = True
                                self.nhiem_vu['Hoàn thành'] = True
                                print(f"[{self.acc_name}] Đã gửi nhiệm vụ xong!")
                            except Exception as e:
                                print(f"[{self.acc_name}] Lỗi khi gửi tin nhắn: {e}")
                                driver.save_screenshot(f"{self.acc_name}_error_message.png")
                                continue
                    if self.stop_event.is_set():
                        remove_proxy_from_profile(self.profile_path)
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
                        return "close"
                    if self.mode == "auto" and len(self.list_url) > 0:
                        count_join_success = 0
                        for url in self.list_url:
                            if url not in self.list_join_success:
                                if logic_join_url_discord(driver, self.acc_name, url,stop_event=self.stop_event) == False:
                                    print(f"[{self.acc_name}] Không thể tham gia vào URL: {url}. Đang thử lại...")
                                    continue
                                else:
                                    driver.get("https://discord.com/login")
                                    if wait_for_any_xpath_or_url(driver, ['//button[@type="submit" and .//div[text()="Log In"]]', 
                                                                          '//div[contains(text(), "Find or start a conversation")]', '//button[@type="submit" and .//div[text()="Log in"]]'],
                                                                            130, 0.5, url="https://discord.com/channels/@me",stop_event=self.stop_event) == None:
                                        print(f"[{self.acc_name}] Không tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Restarting...")
                                        self.list_count_error['wait_for_any_xpath_or_url'] += 1
                                        continue
                                    print("Đã load xong")
                                    if "https://discord.com/channels/@me" not in driver.current_url and logic_login_and_reset_password_discord(driver, self.acc_name, wait, self.email, self.password_discord, self.password_hotmail, self.new_password_discord, 
                                                                                                                                               self.secret_2fa, self.sheet_name, self.row, self.SERVICE_ACCOUNT_FILE, self.SHEET_ID,list_count_error=self.list_count_error,stop_event=self.stop_event) == False:
                                        print(f"[{self.acc_name}] Không thể đăng nhập. Đang thử lại...")
                                        self.list_count_error['login'] += 1
                                        flag_closeFireFox = True
                                        break
                                    count_join_success += 1
                                    self.list_join_success.append(url)
                                    print(f"[{self.acc_name}] Đã tham gia vào URL: {url}.")
                        if count_join_success == len(self.list_url):
                            print(f"[{self.acc_name}] Đã tham gia vào tất cả các URL trong danh sách.")
                            break
                        else:
                            print(f"[{self.acc_name}] Không thể tham gia vào tất cả các URL trong danh sách. Đang thử lại...")
                            flag_closeFireFox = True
                            break
                    print("đang chờ 1s")
                    time.sleep(0.5)
                if self.stop_event.is_set():
                    remove_proxy_from_profile(self.profile_path)
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
                    return "close"
            except Exception as e:
                print(f"[{self.acc_name}] Lỗi: {e}")
                self.text_error += f"[{self.acc_name}] Lỗi: {e}\n"
                flag_closeFireFox = True
                driver.save_screenshot(f"{self.acc_name}_error.png")
            if flag_closeFireFox == True:
                self.restart_count += 1
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
                remove_proxy_from_profile(self.profile_path)
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
        if self.stop_event.is_set():
            if driver :
                remove_proxy_from_profile(self.profile_path)
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
            return "close"
        if self.restart_count >= self.restart_max:
            if len(self.list_url) > len(self.list_join_success):
                for url in self.list_url:
                    if url in self.list_join_success:
                        continue
                    else:
                        self.text_error += f"[{self.acc_name}] Không thể tham gia vào URL: {url}. Đang thử lại...\n"
            count_error = 0
            text_error2 = ""
            for list_error in self.list_count_error:
                if self.list_count_error[list_error] >= 3 and list_error != 'wait_for_any_xpath_or_url':
                    if list_error == "sign_in_hotmail":
                        self.text_error += f"[{self.acc_name}] Không thể đăng nhập vào Hotmail. Đang thử lại...\n"
                    elif list_error == "click_latest_password_reset_email":
                        self.text_error += f"[{self.acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...\n"
                    elif list_error == "edit_sheet_password_discord":
                        self.text_error += f"[{self.acc_name}] Không thể cập nhật mật khẩu trong Google Sheets. Đang thử lại...\n"
                    elif list_error == "login":
                        self.text_error += f"[{self.acc_name}] Không thể đăng nhập. Đang thử lại...\n"
                    elif list_error == "input_2fa":
                        self.text_error += f"[{self.acc_name}] Không thể nhập mã 2FA. Đang thử lại...\n"
                    elif list_error == "logic_resset_password":
                        self.text_error += f"[{self.acc_name}] Không thể reset password. Đang thử lại...\n"
                    count_error += 1
                if self.list_count_error[list_error] > 0:
                    if list_error == "sign_in_hotmail":
                        text_error2 += f"[{self.acc_name}] Không thể đăng nhập vào Hotmail. Đang thử lại...\n"
                    elif list_error == "click_latest_password_reset_email":
                        text_error2 += f"[{self.acc_name}] Không thể click vào email gần đây nhất. Đang thử lại...\n"
                    elif list_error == "edit_sheet_password_discord":
                        text_error2 += f"[{self.acc_name}] Không thể cập nhật mật khẩu trong Google Sheets. Đang thử lại...\n"
                    elif list_error == "login":
                        text_error2 += f"[{self.acc_name}] Không thể đăng nhập. Đang thử lại...\n"
                    elif list_error == "input_2fa":
                        text_error2 += f"[{self.acc_name}] Không thể nhập mã 2FA. Đang thử lại...\n"
                    elif list_error == "logic_resset_password":
                        text_error2 += f"[{self.acc_name}] Không thể reset password. Đang thử lại...\n"
                    elif list_error == "wait_for_any_xpath_or_url":
                        text_error2 += f"[{self.acc_name}] Không thể tìm thấy nút 'Log In' hoặc 'Find or start a conversation'. Đang thử lại...\n"
            if count_error == 0:
                self.text_error += text_error2
            write_error_to_file(self.log_file[0], self.log_file[1], self.acc_name, self.text_error)
            return False
        return True