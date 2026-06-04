from selenium.webdriver.common.by import By
import time
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException

import os


class Common:

    def __init__(self, driver):
        self.driver = driver

    def click(self, xpath):
        self.driver.find_element(By.XPATH, xpath).click()

    def input(self, xpath, value):
        element = self.driver.find_element(By.XPATH, xpath)
        element.clear()
        element.send_keys(value)

    def exists(self, xpath):
        return len(self.driver.find_elements(By.XPATH, xpath)) > 0

    def wait_exists(self, xpath, retry=3, sleep=5):
        for _ in range(retry):
            if self.exists(xpath):
                return True
            time.sleep(sleep)
        return False

    def log(self, message):
        try:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            current_date = now.strftime("%Y-%m-%d")

            log_entry = f"[{timestamp}] {message}"

            print(log_entry)

            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)

            log_file_path = os.path.join(log_dir, f"log_{current_date}.log")

            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")

        except Exception as e:
            print(f"[LOG ERROR] {message} | {e}")

    def select_option(self, xpath, value):
        from selenium.webdriver.support.ui import Select
        select_element = self.driver.find_element(By.XPATH, xpath)
        select = Select(select_element)
        select.select_by_visible_text(str(value))

    def get_value(self, xpath, retry=3, sleep=1):
        for _ in range(retry):
            try:
                element = self.driver.find_element(By.XPATH, xpath)
                value = element.get_attribute("value")

                if value is not None:
                    return value

            except NoSuchElementException:
                pass

            time.sleep(sleep)

        return ""