from activities.BaseActivity import BaseActivity
from config import GOOGLE_APPLICATION_ACCESS_KEY, GOOGLE_APP_ID


class ConnectGoogleAppSheetActivity(BaseActivity):

    NAME = "ConnectGoogleAppSheetActivity"

    DESCRIPTION = """
    Kết nối Google Sheets và lưu API vào Execution Context.
    """

    PARAMETERS = {}

    EXAMPLES = [
        "Kết nối Google Sheets"
    ]

    @staticmethod
    def execute(context, api):
        api.authenticate(
            GOOGLE_APPLICATION_ACCESS_KEY,
            GOOGLE_APP_ID
        )

        context["google_sheet"] = api

        return api