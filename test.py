# from apis.google_app_sheet_api import GoogleAppSheetAPI

# from activities import *

# api = GoogleAppSheetAPI()

# ConnectGoogleAppSheetActivity.execute(api)

# data = ReadGoogleAppSheetDataActivity.execute(
#     api,
#     "Đơn Hàng"
# )

# print(data)
import requests
from config import GOOGLE_APP_SCRIPT_ID
from common import Common
from activities import *
API_URL = f"https://script.google.com/macros/s/{GOOGLE_APP_SCRIPT_ID}/exec"
common = Common(None)
common.log("Đang gọi API để lấy dữ liệu từ Google Sheet...")
print(f"API_URL: {API_URL}")
data = ReadGoogleSheetAppScriptActivity.read_range(API_URL)