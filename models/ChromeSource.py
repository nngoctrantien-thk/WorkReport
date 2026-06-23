from enum import Enum


class ChromeSource(str, Enum):
    API = "chrome_api"
    UI = "ui_automation"
    SELENIUM = "selenium"