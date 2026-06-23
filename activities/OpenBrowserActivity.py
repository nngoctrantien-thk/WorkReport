from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from activities.BaseActivity import BaseActivity
from config import CHROME_PROFILE_PATH
import os


# class OpenBrowserActivity(BaseActivity):

#     NAME = "OpenBrowserActivity"

#     DESCRIPTION = """
#     Mở trình duyệt Chrome bằng Selenium.
#     Có thể mở một URL, sử dụng Chrome Profile và chạy ở chế độ Headless.
#     """

#     PARAMETERS = {
#         "url": {
#             "type": "string",
#             "description": "URL cần mở.",
#             "required": False
#         },
#         "profile_path": {
#             "type": "string",
#             "description": "Đường dẫn Chrome User Profile.",
#             "required": False
#         },
#         "headless": {
#             "type": "boolean",
#             "description": "Chạy Chrome ở chế độ headless.",
#             "required": False,
#             "default": False
#         }
#     }

#     EXAMPLES = [
#         "Mở Chrome",
#         "Mở https://google.com",
#         "Mở Chrome bằng profile mặc định",
#         "Mở Chrome headless"
#     ]

#     @staticmethod
#     def execute(
#         context=None,
#         url=None,
#         profile_path=None,
#         headless=False
#     ):
#         options = Options()

#         options.add_argument("--remote-allow-origins=*")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--start-maximized")
        
#         # --- THÊM 2 DÒNG NÀY ĐỂ TRÁNH CRASH ---
#         options.add_argument("--no-sandbox")
#         options.add_argument("--disable-dev-shm-usage")

#         if headless:
#             options.add_argument("--headless=new")

#         profile = profile_path or CHROME_PROFILE_PATH

#         if profile:
#             os.makedirs(profile, exist_ok=True)
#             options.add_argument(f"--user-data-dir={profile}")
#             # Mẹo: Nên chỉ định thêm một folder profile con để tránh chiếm dụng profile gốc của máy
#             # options.add_argument("--profile-directory=AutomationProfile")

#         driver = webdriver.Chrome(options=options)

#         if url:
#             driver.get(url)
#         else:
#            url = ""

#         if context is not None:
#             context["driver"] = driver

#         return f"Browser {url} opened successfully"
from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class OpenBrowserActivity(BaseActivity):

    NAME = "OpenBrowserActivity"
    DESCRIPTION = """
    Mở một cửa sổ trình duyệt Chrome mới độc lập bằng Selenium.
    Có thể mở một URL chỉ định, sử dụng Chrome Profile và chạy ở chế độ ẩn danh (Headless).
    """

    PARAMETERS = {
        "url": {
            "type": "string",
            "description": "URL cần mở ngay khi khởi chạy trình duyệt.",
            "required": False
        },
        "profile_path": {
            "type": "string",
            "description": "Đường dẫn thư mục lưu trữ Chrome User Profile.",
            "required": False
        },
        "headless": {
            "type": "boolean",
            "description": "Chạy Chrome ngầm ở chế độ headless (Không hiện giao diện).",
            "required": False,
            "default": False
        }
    }

    EXAMPLES = [
        "Mở Chrome",
        "Mở trang https://google.com",
        "Mở Chrome bằng profile mặc định",
        "Mở Chrome ẩn danh headless"
    ]

    @staticmethod
    def execute(context=None, url=None, profile_path=None, headless=False, **kwargs):
        user_id = kwargs.get("user_id", "global")

        if not url and context and "last_extracted_url" in context:
            url = context["last_extracted_url"]
            print(f"[OpenBrowser] Tự động lấy URL từ bộ nhớ chung: {url}")
        # Khởi tạo ChromeManager và ra lệnh mở
        manager = ChromeManager(context=context, user_id=user_id)
        manager.launch_browser(
            url=url, 
            profile_path=profile_path, 
            headless=headless
        )

        display_url = f" tới địa chỉ '{url}'" if url else ""
        return f"🚀 Khởi chạy thành công một cửa sổ trình duyệt Chrome mới{display_url}."