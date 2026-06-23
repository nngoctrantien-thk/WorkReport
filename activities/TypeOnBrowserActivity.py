import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class TypeOnBrowserActivity(BaseActivity):

    NAME = "TypeOnBrowserActivity"
    DESCRIPTION = """
    Nhập dữ liệu văn bản vào một ô nhập liệu (Input, Textarea) trên trang web đang mở bằng Selenium.
    Có tùy chọn tự động xóa sạch nội dung cũ trong ô trước khi nhập chuỗi mới.
    """

    PARAMETERS = {
        "selector": {
            "type": "string",
            "description": "Selector dạng CSS hoặc đường dẫn XPath của ô nhập liệu cần điền văn bản.",
            "required": True
        },
        "text": {
            "type": "string",
            "description": "Nội dung chuỗi văn bản cần nhập vào.",
            "required": True
        },
        "clear_before": {
            "type": "boolean",
            "description": "Xóa sạch chữ đang có sẵn trong ô nhập liệu trước khi gõ chữ mới hay không.",
            "required": False,
            "default": True
        }
    }

    EXAMPLES = [
        "Nhập 'điện thoại iPhone 15' vào ô tìm kiếm",
        "Điền tài khoản admin vào selector #username",
        "Gõ mật khẩu vào ô nhập liệu có xpath //input[@type='password']",
        "Nhập nội dung phản hồi vào ô textarea"
    ]

    @staticmethod
    def execute(context=None, selector=None, text="", clear_before=True, **kwargs):
        user_id = kwargs.get("user_id", "global")

        if not selector:
            return "❌ Thất bại: Thiếu tham số 'selector' để xác định ô nhập liệu."

        # Tầng 1: Lấy driver sẵn có từ RAM bộ nhớ chung (context)
        driver = context.get("driver") if context else None

        # Tầng 2: Thử cứu vớt qua cổng Debug 9222 nếu context bị trống driver
        if not driver:
            try:
                options = Options()
                options.debugger_address = "127.0.0.1:9222"
                driver = webdriver.Chrome(options=options)
                if context is not None:
                    context["driver"] = driver
            except Exception as e:
                return f"❌ Không thể kết nối với trình duyệt Chrome. Lỗi: {str(e)}"

        try:
            # Tự động phân tích loại Selector
            if selector.startswith("/") or selector.startswith("./") or selector.startswith("("):
                by_type = By.XPATH
            else:
                by_type = By.CSS_SELECTOR

            # Tìm phần tử ô nhập liệu
            element = driver.find_element(by_type, selector)

            # Cuộn màn hình tới phần tử
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)

            # Xử lý xóa text cũ nếu được yêu cầu
            if clear_before:
                element.clear()

            # Thực hiện gõ văn bản
            element.send_keys(str(text))
            return f"⌨️ Đã điền thành công nội dung văn bản vào phần tử '{selector}'."

        except Exception as e:
            return f"❌ Lỗi khi thực hiện nhập liệu vào phần tử '{selector}': {str(e)}"