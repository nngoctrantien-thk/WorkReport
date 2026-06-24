import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class SendHostKeyOnBrowserActivity(BaseActivity):

    NAME = "SendHostKeyOnBrowserActivity"
    DESCRIPTION = """
    Gửi các phím chức năng hệ thống (ENTER, TAB, ESCAPE...) hoặc các tổ hợp phím tắt (CTRL+V, SHIFT+TAB...) 
    đến trình duyệt Chrome đang mở. Hỗ trợ gửi trực tiếp vào phần tử cụ thể qua selector hoặc gửi toàn cục 
    vào ô đang được focus hiện tại.
    """

    PARAMETERS = {
        "key": {
            "type": "string",
            "description": "Tên phím hoặc tổ hợp phím cần gửi (Ví dụ: 'ENTER', 'TAB', 'ESCAPE', 'CTRL+A', 'CTRL+V'). Không phân biệt hoa thường.",
            "required": True
        },
        "selector": {
            "type": "string",
            "description": "Selector dạng CSS hoặc XPath của phần tử cần nhận phím. Nếu không truyền, phím sẽ được gửi vào vị trí con trỏ chuột đang focus hiện tại.",
            "required": False,
            "default": None
        },
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab cần gửi phím (1, 2, 3...).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa tiêu đề hoặc URL để nhận diện tab cần gửi phím.",
            "required": False,
            "default": None
        },
        "remote_port": {
            "type": "integer",
            "description": "Cổng Debug của Chrome đang chạy",
            "required": False,
            "default": 9222
        }
    }

    EXAMPLES = [
        "Nhấn nút ENTER trên trình duyệt",
        "Gửi tổ hợp phím CTRL+A vào selector #username",
        "Nhấn phím TAB ở tab số 3",
        "Gửi phím ESCAPE để đóng popup"
    ]

    # Bản đồ ánh xạ các chuỗi ký tự thông dụng sang mã Keys của Selenium
    SELENIUM_KEY_MAP = {
        "ENTER": Keys.ENTER,
        "RETURN": Keys.RETURN,
        "TAB": Keys.TAB,
        "ESCAPE": Keys.ESCAPE,
        "ESC": Keys.ESCAPE,
        "SPACE": Keys.SPACE,
        "BACKSPACE": Keys.BACKSPACE,
        "BACK_SPACE": Keys.BACKSPACE,
        "DELETE": Keys.DELETE,
        "DEL": Keys.DELETE,
        "ARROW_DOWN": Keys.ARROW_DOWN,
        "DOWN": Keys.ARROW_DOWN,
        "ARROW_UP": Keys.ARROW_UP,
        "UP": Keys.ARROW_UP,
        "ARROW_LEFT": Keys.ARROW_LEFT,
        "LEFT": Keys.ARROW_LEFT,
        "ARROW_RIGHT": Keys.ARROW_RIGHT,
        "RIGHT": Keys.ARROW_RIGHT,
        "PAGE_UP": Keys.PAGE_UP,
        "PAGE_DOWN": Keys.PAGE_DOWN,
        "HOME": Keys.HOME,
        "END": Keys.END,
        "F1": Keys.F1, "F2": Keys.F2, "F3": Keys.F3, "F4": Keys.F4,
        "F5": Keys.F5, "F6": Keys.F6, "F7": Keys.F7, "F8": Keys.F8,
        "F9": Keys.F9, "F10": Keys.F10, "F11": Keys.F11, "F12": Keys.F12,
    }

    @staticmethod
    def execute(context=None, key=None, selector=None, index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")

        if not key:
            return "❌ Thất bại: Thiếu tham số 'key' để xác định phím cần gửi."

        # Khởi tạo ChromeManager và xác định đúng Tab đích cần tương tác
        manager = ChromeManager(context=context, remote_port=remote_port, user_id=user_id)
        target_tab, _ = manager.find_tab_by_target(index=index, keyword=keyword)

        # Kết nối tới Driver trình duyệt (Ưu tiên RAM Context -> Cổng Debug)
        driver = context.get("driver") if context else None
        if not driver:
            try:
                options = Options()
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
                driver = webdriver.Chrome(options=options)
                if context is not None:
                    context["driver"] = driver
            except Exception as e:
                return f"❌ Không thể kết nối với trình duyệt Chrome qua cổng {remote_port}. Lỗi: {str(e)}"

        try:
            # Điều hướng luồng điều khiển sang đúng Tab handle mục tiêu nếu tìm thấy
            if target_tab and target_tab.handle:
                try:
                    driver.switch_to.window(target_tab.handle)
                except Exception:
                    pass

            # Xác định phần tử đích để gửi phím (nếu có truyền selector)
            element = None
            if selector:
                if selector.startswith("/") or selector.startswith("./") or selector.startswith("("):
                    by_type = By.XPATH
                else:
                    by_type = By.CSS_SELECTOR
                
                element = driver.find_element(by_type, selector)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.1)

            # =================================================================
            # ⚙️ LOGIC PHÂN TÍCH VÀ GỬI TỔ HỢP PHÍM (HOTKEY PARSER)
            # =================================================================
            key_raw = str(key).upper().strip()
            parts = [p.strip() for p in key_raw.split("+")]

            actions = ActionChains(driver)
            # Nếu có element cụ thể, click nhẹ một cái để kích hoạt focus trước khi bấm phím
            if element:
                actions.click(element)

            modifiers_down = []
            has_normal_key = False

            for part in parts:
                if part in ["CONTROL", "CTRL"]:
                    actions.key_down(Keys.CONTROL)
                    modifiers_down.append(Keys.CONTROL)
                elif part == "SHIFT":
                    actions.key_down(Keys.SHIFT)
                    modifiers_down.append(Keys.SHIFT)
                elif part == "ALT":
                    actions.key_down(Keys.ALT)
                    modifiers_down.append(Keys.ALT)
                else:
                    # Nếu là phím chức năng nằm trong map thì bốc ra, ngược lại coi như ký tự thường (v dụ: 'A', 'V')
                    target_key = SendHostKeyOnBrowserActivity.SELENIUM_KEY_MAP.get(part, part.lower())
                    actions.send_keys(target_key)
                    has_normal_key = True

            # Giải phóng (nhả) các phím chức năng hệ thống theo thứ tự ngược lại để tránh kẹt phím
            for mod in reversed(modifiers_down):
                actions.key_up(mod)

            # Kích hoạt lệnh thực thi chuỗi phím bấm lên trình duyệt
            actions.perform()
            
            target_desc = f"vào phần tử '{selector}'" if selector else "vào vị trí đang focus"
            return f"⌨️ Đã gửi thành công phím/tổ hợp phím '{key_raw}' {target_desc}."

        except Exception as e:
            return f"❌ Lỗi khi thực hiện gửi phím '{key}' lên trình duyệt: {str(e)}"