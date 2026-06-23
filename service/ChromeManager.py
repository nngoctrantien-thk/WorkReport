import http.client
import json
import time
import psutil
import win32process
import re
from pathlib import Path
from models.ChromeTab import ChromeTab
from models.ChromeSource import ChromeSource

from service.CacheManager import CacheManager
from service.Logger import get_logger

from utils.FileUtils import FileUtils
from utils.TextUtils import TextUtils

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from config import CHROME_PROFILE_PATH
import os
# Nạp các thư viện tùy chọn hệ thống (Windows)
try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None

try:
    import win32clipboard
except ImportError:
    win32clipboard = None


logger = get_logger(__name__)


class ChromeManager:
    def __init__(
        self,
        driver=None,
        context=None,
        logger=None,
        api_client=None,
        remote_port=9222,
        user_id=None,
    ):
        self.driver = driver
        self.context = context
        self.logger = logger
        self.api_client = api_client
        self.remote_port = remote_port
        self.user_id = user_id or "global"
        self._tab_cache = {}

    # ==========================================================
    # Debug API Core
    # ==========================================================

    def _request(self, path: str):
        conn = http.client.HTTPConnection(
            "127.0.0.1",
            self.remote_port,
            timeout=2
        )
        conn.request("GET", path)
        response = conn.getresponse()

        if response.status != 200:
            raise RuntimeError(
                f"Chrome Debug API error : {response.status}"
            )

        return json.loads(
            response.read().decode("utf8")
        )

    def get_tabs_api(self):
        tabs = []
        try:
            targets = self._request("/json/list")
            for target in targets:
                if target.get("type") != "page":
                    continue

                tabs.append(
                    ChromeTab(
                        handle=target.get("id"),
                        title=target.get("title", "No Title"),
                        url=target.get("url", ""),
                        source=ChromeSource.API
                    )
                )
        except Exception as e:
            logger.exception(e)

        return tabs

    # ==========================================================
    # UI Automation Core
    # ==========================================================

    def chrome_windows(self):
        if Desktop is None:
            return []

        windows = []
        try:
            all_windows = Desktop(backend="uia").windows(
                class_name="Chrome_WidgetWin_1"
            )

            for win in all_windows:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(win.handle)
                    process = psutil.Process(pid)

                    if process.name().lower() != "chrome.exe":
                        continue

                    windows.append(win)
                except Exception:
                    continue
        except Exception as e:
            logger.exception(e)

        return windows

    def get_tabs_ui(self):
        tabs = []
        for window in self.chrome_windows():
            try:
                items = window.descendants(control_type="TabItem")
                for item in items:
                    title = item.window_text().strip()

                    if not title or title == "Lưu lượng truy cập mạng":
                        continue

                    tabs.append(
                        ChromeTab(
                            handle=None,
                            title=title,
                            url="",
                            source=ChromeSource.UI
                        )
                    )
            except Exception as e:
                logger.exception(e)

        return tabs

    # ==========================================================
    # Merge & Scan Public API
    # ==========================================================

    def get_all_tabs(self):
        api_tabs = self.get_tabs_api()
        if api_tabs:
            return api_tabs
        return self.get_tabs_ui()

    def scan(self, context=None, user_id=None):
        tabs = []
        tabs.extend(self.get_tabs_api())
        tabs.extend(self.get_tabs_ui())

        # Sửa lỗi phạm vi biến: Ưu tiên tham số hàm -> Thuộc tính khởi tạo -> Giá trị mặc định
        active_context = context if context is not None else self.context
        active_user_id = user_id if user_id is not None else self.user_id

        if active_context is not None:
            active_context["chrome_tabs"] = tabs

        self.save_cache(active_user_id, tabs)
        return tabs

    # ==========================================================
    # Telegram Format Utility
    # ==========================================================

    def format_telegram(self, tabs):
        if not tabs:
            return "❌ Không tìm thấy Google Chrome đang mở."

        lines = []
        for i, tab in enumerate(tabs, start=1):
            title = TextUtils.sanitize(tab.title)
            url = TextUtils.sanitize(tab.url)

            if url:
                lines.append(f"{i}. 📌 Tiêu đề: {title}\n🔗 Link: {url}")
            else:
                lines.append(f"{i}. 📌 Tab: {title}")

        return f"🤖 DANH SÁCH TAB CHROME ({len(tabs)} tab)\n\n" + "\n\n".join(lines)

    # ==========================================================
    # Cache Management
    # ==========================================================

    def cache_path(self, user_id):
        return FileUtils.tab_cache(user_id)

    def save_cache(self, user_id, tabs):
        CacheManager.save(
            self.cache_path(user_id),
            [tab.to_dict() for tab in tabs]
        )

    def load_cache(self, user_id):
        raw = CacheManager.load(self.cache_path(user_id), [])
        tabs = []
        for item in raw:
            try:
                tabs.append(ChromeTab.from_dict(item))
            except Exception:
                continue
        return tabs

    def clear_cache(self, user_id):
        CacheManager.clear_json(self.cache_path(user_id))

    # ==========================================================
    # Context Management
    # ==========================================================

    @staticmethod
    def save_context(context, tabs):
        if context is None:
            return
        context["chrome_tabs"] = tabs

    @staticmethod
    def load_context(context):
        if context is None:
            return []
        return context.get("chrome_tabs", [])

    @staticmethod
    def _normalize(text):
        if not text:
            return ""
        return TextUtils.sanitize(text).lower().strip()

    # ==========================================================
    # Centralized Discovery (Dành cho Activity Phân Tích)
    # ==========================================================

    def find_tab_by_target(self, index=None, keyword=None):
        """
        Tự động kiểm tra Context & Cache để tìm kiếm một Object ChromeTab cụ thể.
        Trả về tuple: (ChromeTab, error_message)
        """
        saved_tabs = self.load_context(self.context)
        if not saved_tabs:
            saved_tabs = self.load_cache(self.user_id)

        if not saved_tabs:
            return None, "❌ Chưa có dữ liệu tab. Vui lòng chạy lệnh kiểm tra danh sách tab trước."

        # Tìm theo số thứ tự index
        if index is not None:
            try:
                target_idx = int(index) - 1
                if 0 <= target_idx < len(saved_tabs):
                    return saved_tabs[target_idx], None
                return None, f"❌ Vị trí {index} không hợp lệ. Chỉ có từ 1 đến {len(saved_tabs)}."
            except Exception:
                return None, "❌ Chỉ số 'index' truyền vào phải là một số nguyên."

        # Tìm theo từ khóa keyword
        if keyword:
            kw = self._normalize(keyword)
            for tab in saved_tabs:
                title = self._normalize(tab.title if hasattr(tab, 'title') else tab.get("title", ""))
                url = self._normalize(tab.url if hasattr(tab, 'url') else tab.get("url", ""))
                if kw in title or kw in url:
                    # Đảm bảo trả ra định dạng Object ChromeTab chuẩn
                    if isinstance(tab, dict):
                        return ChromeTab.from_dict(tab), None
                    return tab, None
            return None, f"❌ Không tìm thấy tab nào chứa từ khóa: '{keyword}'"

        return None, "❌ Vui lòng truyền tham số 'index' hoặc 'keyword' để chỉ định tab."

    # ==========================================================
    # Text Extraction (Dành cho Activity Phân Tích)
    # ==========================================================

    def extract_tab_text(self, tab: ChromeTab):
        """
        Trích xuất dữ liệu văn bản thô từ trang web (Ưu tiên Selenium -> Fallback UI Automation)
        """
        if not tab:
            return ""

        web_text_content = ""
        source_str = tab.source.value if hasattr(tab.source, 'value') else str(tab.source)

        # --- Cách A: Nếu tab có Handle và hệ thống mở cổng Debug Port ---
        if source_str in ["chrome_api", "selenium"] and tab.handle:
            driver = self.context.get("driver") if self.context else None
            is_temp_driver = False
            try:
                if not driver:
                    options = Options()
                    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.remote_port}")
                    driver = webdriver.Chrome(options=options)
                    is_temp_driver = True

                driver.switch_to.window(tab.handle)
                web_text_content = driver.find_element(By.TAG_NAME, "body").text

                if is_temp_driver:
                    driver.quit()
            except Exception as e:
                logger.error(f"[ChromeManager] Lỗi bóc dữ liệu bằng Selenium: {str(e)}")

        # --- Cách B: Fallback sao chép màn hình qua UI Automation (Khi không bật Debug Port) ---
        if not web_text_content and Desktop is not None and win32clipboard is not None:
            try:
                windows = self.chrome_windows()
                for win in windows:
                    tab_items = win.descendants(control_type="TabItem")
                    for tab_item in tab_items:
                        if self._normalize(tab_item.window_text()) == self._normalize(tab.title):
                            win.set_focus()
                            tab_item.click_input()
                            time.sleep(0.5)
                            win.click_input()
                            time.sleep(0.3)
                            win.type_keys('^a^c') # Ctrl+A & Ctrl+C
                            time.sleep(0.5)

                            win32clipboard.OpenClipboard()
                            web_text_content = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                            win32clipboard.CloseClipboard()
                            break
                    if web_text_content:
                        break
            except Exception as e:
                logger.error(f"[ChromeManager] Lỗi cào text bằng UI Automation: {str(e)}")

        return web_text_content

    # ==========================================================
    # Close Tab Logic
    # ==========================================================

    def close_tab(self, tab):
        if tab is None:
            return False

        logger.info("Close tab : %s", tab.title)

        if tab.source == ChromeSource.API and self.close_by_api(tab):
            return True

        if self.close_by_selenium(tab):
            return True

        if self.close_by_ui(tab):
            return True

        return False

    def close_by_api(self, tab):
        if not tab.handle:
            return False

        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.remote_port, timeout=2)
            conn.request("GET", f"/json/close/{tab.handle}")
            response = conn.getresponse()
            return response.status == 200
        except Exception as e:
            logger.exception(e)
            return False

    def close_by_selenium(self, tab):
        if not tab.url:
            return False

        driver = None
        try:
            options = Options()
            options.debugger_address = f"127.0.0.1:{self.remote_port}"
            driver = webdriver.Chrome(options=options)

            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if driver.current_url == tab.url:
                    driver.close()
                    return True
        except Exception as e:
            logger.exception(e)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        return False

    def close_by_ui(self, tab):
        if Desktop is None:
            return False

        title = self._normalize(tab.title)
        try:
            for window in self.chrome_windows():
                items = window.descendants(control_type="TabItem")
                for item in items:
                    name = self._normalize(item.window_text())
                    if name != title:
                        continue

                    try:
                        item.select()
                    except Exception:
                        pass

                    try:
                        window.type_keys("^w", set_foreground=True)
                        return True
                    except Exception:
                        continue
        except Exception as e:
            logger.exception(e)

        return False

    def update_cache_after_close(self, user_id, tab):
        tabs = self.load_cache(user_id)
        new_tabs = []
        removed = False

        for item in tabs:
            if removed:
                new_tabs.append(item)
                continue

            same_title = self._normalize(item.title) == self._normalize(tab.title)
            same_url = self._normalize(item.url) == self._normalize(tab.url)

            if same_title and same_url:
                removed = True
                continue

            new_tabs.append(item)

        self.save_cache(user_id, new_tabs)
        return new_tabs

    def get_tab_url(self, tab: ChromeTab):
        """
        Lấy URL của tab. 
        - Tầng 1: Nếu tab đã có URL, trả về luôn.
        - Tầng 2: Thử kết nối Selenium qua cổng Debug để lấy URL theo Tiêu đề (Đã tối ưu chống treo).
        - Tầng 3: Nếu sập cổng Debug, quét qua Chrome thật, tìm tab, click chọn và sao chép thanh địa chỉ.
        """
        if not tab:
            return ""
        
        # [TẦNG 1] Nếu tab đã có sẵn URL (Quét từ Debug API), trả về luôn
        if tab.url:
            return tab.url
        
        # [TẦNG 2] Dò tìm bằng Selenium qua cổng Debug 9222
        # TỐI ƯU 1: Kiểm tra port trước, nếu không hoạt động hoặc là Edge thì bỏ qua Selenium luôn
        if hasattr(self, '_is_chrome_debug_active') and self._is_chrome_debug_active():
            driver = None
            try:
                options = Options()
                options.debugger_address = f"127.0.0.1:{self.remote_port}"
                options.add_experimental_option("excludeSwitches", ["enable-logging"]) # Tắt log rác của Selenium
                
                driver = webdriver.Chrome(options=options)
                
                # Duyệt qua các tab đang mở trong Chrome để tìm tab trùng tiêu đề
                for handle in driver.window_handles:
                    try:
                        # TỐI ƯU 2: Bọc độc lập từng handle, né tab bị treo hoặc dính Alert dialogue
                        driver.switch_to.window(handle)
                        if self._normalize(driver.title) == self._normalize(tab.title):
                            return driver.current_url
                    except Exception:
                        continue # Bỏ qua tab lỗi, tiếp tục quét các tab còn lại
            except Exception as e:
                logger.warning(f"[ChromeManager] Selenium gặp lỗi khi kết nối hoặc duyệt tìm URL: {str(e)}")
            finally:
                if driver:
                    try:
                        driver.quit() # Giải phóng session driver cục bộ an toàn
                    except Exception:
                        pass
        else:
            logger.info("[ChromeManager] Cổng Debug 9222 đóng hoặc thuộc về Edge. Nhảy thẳng xuống Tầng 3 UI Automation.")
        
        # [TẦNG 3] CHỮA CHÁY BẰNG UI AUTOMATION (Quét trực tiếp trên Chrome thật)
        if Desktop is not None and win32clipboard is not None:
            try:
                for win in self.chrome_windows():
                    tab_items = win.descendants(control_type="TabItem")
                    
                    for tab_item in tab_items:
                        if self._normalize(tab_item.window_text()) == self._normalize(tab.title):
                            win.set_focus()         
                            tab_item.click_input()  
                            time.sleep(0.3)
                            win.click_input()       
                            time.sleep(0.2)
                            
                            # Gửi tổ hợp phím lấy URL
                            win.type_keys('^l^c')
                            time.sleep(0.4)
                            
                            # TỐI ƯU 3: Đọc dữ liệu Clipboard an toàn tuyệt đối bằng try...finally
                            win32clipboard.OpenClipboard()
                            try:
                                url_copied = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                            finally:
                                win32clipboard.CloseClipboard() # Luôn luôn giải phóng Clipboard kể cả khi lỗi
                            
                            if url_copied and (url_copied.startswith("http") or url_copied.startswith("chrome")):
                                return url_copied.strip()
            except Exception as ue:
                logger.error(f"[ChromeManager] Lỗi nghiêm trọng khi bóc tách URL bằng phím tắt UI: {str(ue)}")
                    
        return ""

    def launch_browser(self, url=None, profile_path=None, headless=False):
        """
        Khởi chạy một thực thể Google Chrome mới bằng Selenium.
        Tự động sửa lỗi template hệ thống và lọc sạch chữ tiếng Việt dính vào đuôi URL.
        """

        # =================================================================
        # VŨ KHÍ 1: SỬA LỖI TEMPLATE STRING CỦA AI ROUTER
        # Nếu url truyền vào là chuỗi rác template chưa được giải mã của hệ thống
        # =================================================================
        if url and ("{" in str(url) or "}" in str(url) or "GetChromeTabUrlActivity" in str(url)):
            logger.warning(f"[ChromeManager] Phát hiện chuỗi template lỗi: '{url}'. Tiến hành hủy bỏ để ép lấy từ Context.")
            url = None 

        # Nếu không có URL hoặc URL bị lỗi template ở trên, chủ động bốc từ RAM dùng chung (Context)
        if not url and self.context and "last_extracted_url" in self.context:
            url = self.context["last_extracted_url"]
            logger.info(f"[ChromeManager] Đã lấy URL thành công từ bộ nhớ RAM Context: {url}")

        # Nếu RAM trống, thử cứu vớt từ Clipboard hệ thống
        if not url and win32clipboard is not None:
            try:
                time.sleep(0.1)
                win32clipboard.OpenClipboard()
                clip_data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                if clip_data:
                    match = re.search(r'(https?://[^\s]+)', str(clip_data))
                    if match:
                        url = match.group(1).strip()
            except Exception:
                pass

        # =================================================================
        # VŨ KHÍ 2: LỌC SẠCH CHỮ TIẾNG VIỆT BỊ DÍNH VÀO ĐUÔI SỐ URL (Ví dụ: 1030480252Xem)
        # =================================================================
        if url and isinstance(url, str):
            url = url.strip()
            # Bước A: Tìm đường link độc lập, cắt bỏ các khoảng trắng phía sau
            match = re.search(r'(https?://[^\s*<>"\x00-\x1f\x7f-\x9f]+)', url)
            if match:
                clean_url = match.group(1).strip()
                
                # Bước B: Xử lý thông minh - Cắt bỏ toàn bộ chữ cái (Xem, qua, truoc) 
                # dính liền ngay sau ký tự số cuối cùng (thường là đuôi gid=123456)
                clean_url = re.sub(r'(?<=\d)[A-Za-zÀ-ỹ]+$', '', clean_url)
                
                url = clean_url
                logger.info(f"[ChromeManager] URL sau khi được lọc sạch rác chữ: {url}")

        # Cấu hình các tham số khởi chạy Selenium ổn định
        options = Options()
        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--hide-crash-restore-bubble")
        options.add_argument("--disable-session-crashed-bubble")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--dont-trigger-profile-browser-signin-flow")

        prefs = {
            "profile.exit_type": "Normal",
            "profile.exited_cleanly": True
        }
        options.add_experimental_option("prefs", prefs)

        if headless:
            options.add_argument("--headless=new")

        # Quản lý Profile
        profile = profile_path or CHROME_PROFILE_PATH
        if profile:
            if r"Microsoft\Edge" in str(profile):
                profile = os.path.join(os.getcwd(), "cache", "chrome_profile")
            os.makedirs(profile, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile}")
            options.add_argument("--profile-directory=Default")

        # Ép chạy đúng file thực thi Chrome
        chrome_binaries = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for binary in chrome_binaries:
            if os.path.exists(binary):
                options.binary_location = binary
                break

        try:
            driver = webdriver.Chrome(options=options)
            
            # Tiến hành điều hướng đến URL đã được làm sạch
            if url and url.startswith("http"):
                time.sleep(0.5) 
                driver.get(url)
                logger.info(f"[ChromeManager] Trình duyệt kích hoạt thành công tới địa chỉ: {url}")
            else:
                logger.warning(f"[ChromeManager] Mở New Tab trống do không tìm thấy URL hợp lệ trong chuỗi luồng.")
                
            self.driver = driver
            if self.context is not None:
                self.context["driver"] = driver
                
            return driver
        except Exception as e:
            logger.error(f"[ChromeManager] Gặp lỗi khi khởi chạy trình duyệt: {str(e)}")
            raise e

    def take_screenshot(self, filename="screenshot.png"):
        """
        Chụp ảnh màn hình thông minh chống crash khi thiếu thư viện PIL.
        """
        from pathlib import Path
        import os
        
        file_path = Path(filename)
        if file_path.parent:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # --- TẦNG 1: CHỤP BẰNG DRIVER SELENIUM (Không phụ thuộc vào PIL) ---
        driver = self.driver or (self.context.get("driver") if self.context else None)
        if driver:
            try:
                driver.save_screenshot(str(file_path))
                logger.info(f"[ChromeManager] Chụp ảnh màn hình bằng Selenium thành công: {filename}")
                return True, f"📸 [Selenium] Chụp ảnh màn hình trình duyệt thành công, đã lưu tại: {filename}"
            except Exception as e:
                logger.warning(f"[ChromeManager] Driver lỗi hoặc đã đóng, chuyển sang fallback UI: {str(e)}")

        # --- TẦNG 2: CHỤP CỬA SỔ ĐANG ACTIVE TRÊN MÀN HÌNH (Cần có Pillow) ---
        if Desktop is not None:
            try:
                import win32gui
                from pywinauto import Application
                
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    win_text = win32gui.GetWindowText(hwnd) or "Cửa sổ ẩn"
                    app = Application().connect(handle=hwnd)
                    win = app.window(handle=hwnd)
                    
                    # Gọi hàm chụp ảnh giao diện ứng dụng
                    img = win.capture_as_image()
                    
                    # SỬA LỖI CRASH: Kiểm tra nghiêm ngặt xem đối tượng ảnh có tồn tại hay không
                    if img is not None:
                        img.save(str(file_path))
                        logger.info(f"[ChromeManager] Chụp ảnh cửa sổ active '{win_text}' thành công.")
                        return True, f"🖥️ [OS UI] Chụp thành công cửa sổ đang active ('{win_text}'), lưu tại: {filename}"
                    else:
                        logger.warning("[ChromeManager] Pywinauto không thể khởi tạo ảnh do thiếu thư viện PIL.")
            except Exception as e:
                logger.error(f"[ChromeManager] Lỗi khi chụp cửa sổ active bằng pywinauto: {str(e)}")

        # --- TẦNG 3: DỰ PHÒNG CHỤP TOÀN MÀN HÌNH (Cần có Pillow) ---
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            if img is not None:
                img.save(str(file_path))
                logger.info("[ChromeManager] Fallback chụp toàn màn hình Fullscreen thành công.")
                return True, f"🖥️ [OS Fullscreen] Chụp toàn bộ màn hình máy tính thành công, lưu tại: {filename}"
        except ModuleNotFoundError:
            logger.error("[ChromeManager] Thất bại hoàn toàn: Máy tính của bạn chưa cài thư viện 'Pillow'. Vui lòng chạy lệnh 'pip install Pillow'.")
        except Exception as e:
            logger.error(f"[ChromeManager] Hạ tầng chụp ảnh OS gặp lỗi: {str(e)}")

        return False, "❌ Thất bại: Thiếu thư viện 'Pillow' để xử lý ảnh chụp màn hình hệ điều hành Windows."