import time
# Nếu hệ thống của bạn yêu cầu tất cả Activity phải kế thừa BaseActivity, 
# hãy mở comment dòng dưới đây ra nhé:
# from activities.BaseActivity import BaseActivity


class DelayActivity: # hoặc class DelayActivity(BaseActivity):

    NAME = "DelayActivity"

    DESCRIPTION = """
    Tạm dừng chương trình trong một khoảng thời gian.
    Thường dùng để chờ website tải, chờ ứng dụng bung giao diện hoặc chờ giữa các bước tự động hóa.
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
    def execute(context=None, seconds=1, **kwargs):
        try:
            sec = float(seconds)
        except (ValueError, TypeError):
            sec = 1.0
            seconds = 1

        time.sleep(sec)
        time.sleep(2)
        return f"⏳ Đã tạm dừng hệ thống thành công trong {seconds} giây."