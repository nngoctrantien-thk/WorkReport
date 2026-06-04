from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class OpenBrowserActivity:

    @staticmethod
    def execute(url = None,profile_path = None, headless = None):

        options = Options()
        options.add_argument("--remote-allow-origins=*")
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        if profile_path:
            options.add_argument(f"--user-data-dir={profile_path}")
        else:
            options.add_argument(
                r"--user-data-dir=C:\chrome-selenium-profile"
            )

        options.add_argument("--start-maximized")

        driver = webdriver.Chrome(options=options)

        if url:
            driver.get(url)

        return driver