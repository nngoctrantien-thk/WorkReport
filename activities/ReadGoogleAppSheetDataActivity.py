from activities.BaseActivity import BaseActivity


class ReadGoogleAppSheetDataActivity(BaseActivity):

    NAME = "ReadGoogleAppSheetDataActivity"

    DESCRIPTION = """
    Đọc dữ liệu từ một Google Sheet.
    Yêu cầu đã kết nối Google Sheets bằng ConnectGoogleAppSheetActivity.
    """

    PARAMETERS = {
        "table_name": {
            "type": "string",
            "description": "Tên sheet cần đọc."
        }
    }

    EXAMPLES = [
        "Đọc sheet Employees",
        "Đọc dữ liệu Sheet1",
        "Lấy toàn bộ dữ liệu từ Users"
    ]

    @staticmethod
    def execute(context, table_name):
        """
        Args:
            context (dict): Execution Context
            table_name (str): Tên Sheet

        Returns:
            list: Danh sách dữ liệu
        """

        api = context.get("google_sheet")

        if api is None:
            raise Exception(
                "Google Sheet chưa được kết nối. "
                "Hãy chạy ConnectGoogleAppSheetActivity trước."
            )

        return api.read_range(table_name)