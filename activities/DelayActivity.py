import time


class DelayActivity:

    NAME = "DelayActivity"

    DESCRIPTION = """
    Tạm dừng chương trình trong một khoảng thời gian.
    Thường dùng để chờ website tải, chờ API hoặc chờ giữa các bước tự động hóa.
    """

    PARAMETERS = {
        "seconds": {
            "type": "number",
            "description": "Số giây cần chờ.",
            "required": True,
            "default": 1
        }
    }

    EXAMPLES = [
        "chờ 5 giây",
        "đợi 10 giây",
        "delay 2 giây",
        "sleep 3 seconds"
    ]

    @staticmethod
    def execute(seconds=1):
        time.sleep(float(seconds))
        return f"Waited {seconds} second(s)."