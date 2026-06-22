from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from activities.BaseActivity import BaseActivity
from config import CHROME_PROFILE_PATH
import os


class OpenBrowserActivity(BaseActivity):

    NAME = "OpenBrowserActivity"

    DESCRIPTION = """
    Mở trình duyệt Chrome bằng Selenium.
    Có thể mở một URL, sử dụng Chrome Profile và chạy ở chế độ Headless.
    """

    PARAMETERS = {
        "url": {
            "type": "string",
            "description": "URL cần mở.",
            "required": False
        },
        "profile_path": {
            "type": "string",
            "description": "Đường dẫn Chrome User Profile.",
            "required": False
        },
        "headless": {
            "type": "boolean",
            "description": "Chạy Chrome ở chế độ headless.",
            "required": False,
            "default": False
        }
    }

    EXAMPLES = [
        "Mở Chrome",
        "Mở https://google.com",
        "Mở Chrome bằng profile mặc định",
        "Mở Chrome headless"
    ]

    @staticmethod
    def execute(
        url=None,
        profile_path=None,
        headless=False
    ):
        options = Options()

        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")

        if headless:
            options.add_argument("--headless=new")

        profile = profile_path or CHROME_PROFILE_PATH

        if profile:
            os.makedirs(profile, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile}")

        driver = webdriver.Chrome(options=options)

        if url:
            driver.get(url)

        return driver