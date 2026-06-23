import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class ClickOnBrowserActivity(BaseActivity):

    NAME = "ClickOnBrowserActivity"
    DESCRIPTION = """
    Click (nhấp chuột) vào một phần tử cụ thể (nút, liên kết, hình ảnh, icon...) trên trang web đang mở bằng Selenium.
    Hỗ trợ tự động nhận diện CSS Selector hoặc XPath và tự động cuộn màn hình đến phần tử trước khi click.
    """

    PARAMETERS = {
        "selector": {
            "type": "string",
            "description": "Selector dạng CSS (ví dụ: #submit-btn, .class-name) hoặc đường dẫn XPath (ví dụ: //button[@id='login']).",
            "required": True
        }
    }

    EXAMPLES = [
        "Click vào nút Tìm kiếm",
        "Nhấp vào phần tử #login-button",
        "Bấm vào nút có xpath //button[@type='submit']",
        "Click chọn thẻ a .nav-link"
    ]

    @staticmethod
    def execute(context=None, selector=None, **kwargs):
        user_id = kwargs.get("user_id", "global")

        if not selector:
            return "❌ Thất bại: Thiếu tham số 'selector' để xác định phần tử cần click."

        # Tầng 1: Lấy driver sẵn có từ RAM bộ nhớ chung (context)
        driver = context.get("driver") if context else None

        # Tầng 2: Nếu context chưa có driver, thử cứu vớt bằng cách bắt vào cổng Debug 9222 của Chrome đang mở
        if not driver:
            try:
                options = Options()
                options.debugger_address = "127.0.0.1:9222"
                driver = webdriver.Chrome(options=options)
                if context is not None:
                    context["driver"] = driver
            except Exception as e:
                return f"❌ Không thể kết nối với trình duyệt Chrome (Đảm bảo Chrome đã mở và bật Debug Port). Lỗi: {str(e)}"

        try:
            # Tự động phân tích và nhận diện loại Selector (XPath hay CSS)
            if selector.startswith("/") or selector.startswith("./") or selector.startswith("("):
                by_type = By.XPATH
            else:
                by_type = By.CSS_SELECTOR

            # Tìm phần tử trên trang
            element = driver.find_element(by_type, selector)

            # Tối ưu: Cuộn màn hình đưa phần tử vào giữa khung nhìn (tránh bị che khuất bởi các phần tử cố định như Header)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)

            # Thực hiện click
            element.click()
            return f"🎯 Đã click thành công vào phần tử '{selector}'."

        except Exception as e:
            return f"❌ Lỗi khi thực hiện hành động click vào phần tử '{selector}': {str(e)}"