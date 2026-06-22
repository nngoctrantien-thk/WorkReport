# from apis.google_app_sheet_api import GoogleAppSheetAPI

# from activities import *

# api = GoogleAppSheetAPI()

# ConnectGoogleAppSheetActivity.execute(api)

# data = ReadGoogleAppSheetDataActivity.execute(
#     api,
#     "Đơn Hàng"
# )

# # print(data)
# import requests
# from config import GOOGLE_APP_SCRIPT_ID
# from common import Common
# from activities import *
# API_URL = f"https://script.google.com/macros/s/{GOOGLE_APP_SCRIPT_ID}/exec"
# common = Common(None)
# common.log("Đang gọi API để lấy dữ liệu từ Google Sheet...")
# print(f"API_URL: {API_URL}")
# data = ReadGoogleSheetAppScriptActivity.read_range(API_URL)
# print(data)

# import os
# from datetime import datetime, timedelta
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By

# from activities import *
# from common import Common
# from service import Service


# deleted = CleanupLogFilesActivity.execute(
#     log_directory="./logs",
#     retention_days=2
# )

# print(f"Deleted {deleted} log files.")
import requests
from config import TELEGRAM_BOT_TOKEN
from service.TelegramService import TelegramService
TelegramService(TELEGRAM_BOT_TOKEN).run()