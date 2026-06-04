import math
from selenium.webdriver.common.by import By

class Service:
    def __init__(self, common):
        self.common = common

    def safe(self, value):
        if value is None:
            return ""
        if isinstance(value, float) and math.isnan(value):
            return ""
        if str(value).lower() == "nan":
            return ""
        return str(value).strip()

    def get_id_model(self):
        return self.common.get_value("(//input[contains(@name,'today_tasks') and @type='search'])[1]")

    def click_ok_if_exists(self):
        if self.common.wait_exists("//button[contains(text(),'OK')]", retry=3, sleep=2):
            self.common.log("Found 'OK' button. Clicking...")
            self.common.click("//button[contains(text(),'OK')]")

    def sequence_tasks(
        self,
        select_task_today,
        task_details_today,
        task_hours_today,
        select_task_tomorrow,
        task_details_tomorrow,
        task_hours_tomorrow,
        index
    ):
        idx = index + 1

        today_select_xpath = f"(//select[contains(@name,'today_tasks')])[{idx}]"
        today_search_xpath = f"(//input[contains(@name,'today_tasks') and @type='search'])[{idx}]"
        today_hours_xpath = f"(//input[contains(@name,'today_tasks') and @type='number'])[{idx}]"

        tomorrow_select_xpath = f"(//select[contains(@name,'tomorrow_tasks')])[{idx}]"
        tomorrow_search_xpath = f"(//input[contains(@name,'tomorrow_tasks') and @type='search'])[{idx}]"
        tomorrow_hours_xpath = f"(//input[contains(@name,'tomorrow_tasks') and @type='number'])[{idx}]"

        # TODAY
        if select_task_today and self.common.exists(today_select_xpath):
            self.common.select_option(today_select_xpath, select_task_today)
            self.common.input(today_search_xpath, task_details_today)
            self.common.input(today_hours_xpath, task_hours_today)
            self.common.log(f"add today's tasks {idx}, details: {task_details_today}, hours: {task_hours_today}")
            
        # TOMORROW
        if select_task_tomorrow and self.common.exists(tomorrow_select_xpath):
            self.common.select_option(tomorrow_select_xpath, select_task_tomorrow)
            self.common.input(tomorrow_search_xpath, task_details_tomorrow)
            self.common.input(tomorrow_hours_xpath, task_hours_tomorrow)
            self.common.log(f"add tomorrow's tasks {idx}, details: {task_details_tomorrow}, hours: {task_hours_tomorrow}")