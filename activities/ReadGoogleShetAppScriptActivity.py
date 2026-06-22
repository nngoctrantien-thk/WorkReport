import requests

from activities.BaseActivity import BaseActivity
from config import GOOGLE_APP_SCRIPT_URL


class ReadGoogleSheetAppScriptActivity(BaseActivity):

    NAME = "ReadGoogleSheetAppScriptActivity"

    DESCRIPTION = """
    Đọc dữ liệu từ Google Sheets thông qua Google Apps Script Web App.
    Trả về danh sách các bản ghi (List[Dict]).
    """

    PARAMETERS = {
        "api_url": {
            "type": "string",
            "description": "Địa chỉ Google Apps Script Web App.",
            "required": False
        }
    }

    EXAMPLES = [
        "Đọc dữ liệu Google Sheet",
        "Lấy danh sách nhân viên từ Google Sheet",
        "Đọc Sheet thông qua Apps Script"
    ]

    @staticmethod
    def execute(api_url=None):

        url = api_url or GOOGLE_APP_SCRIPT_URL

        if not url:
            raise Exception(
                "Chưa cấu hình GOOGLE_APP_SCRIPT_URL."
            )

        try:
            response = requests.get(
                url,
                timeout=30
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.JSONDecodeError:
            raise Exception(
                "Google Apps Script không trả về JSON. "
                "Hãy kiểm tra Web App đã Deploy với quyền 'Anyone' hoặc "
                "'Anyone with the link'."
            )

        except requests.exceptions.Timeout:
            raise Exception(
                "Kết nối tới Google Apps Script bị timeout."
            )

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Lỗi khi gọi Google Apps Script: {e}"
            )