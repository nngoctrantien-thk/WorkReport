import os  # Thêm thư viện os để gọi lệnh hệ thống Windows
from activities.BaseActivity import BaseActivity


class CloseBrowserActivity(BaseActivity):

    NAME = "CloseBrowserActivity"

    DESCRIPTION = """
    Đóng trình duyệt Chrome đang chạy trong phiên làm việc.
    Nếu không tìm thấy driver trong hệ thống (context), tự động cưỡng chế tắt (kill) toàn bộ tiến trình Chrome và ChromeDriver chạy ngầm trên máy.
    """

    PARAMETERS = {}

    EXAMPLES = [
        "Đóng trình duyệt",
        "Tắt Chrome",
        "Đóng Chrome",
        "Kill chrome",
        "Thoát trình duyệt"
    ]

    @staticmethod
    def execute(context=None, **kwargs):
        
        # TRƯỜNG HỢP 1: Có trình duyệt đang mở và liên kết chuẩn chỉ trong phiên chạy này
        if context and "driver" in context:
            driver = context["driver"]
            try:
                driver.quit()
                context.pop("driver", None) # Xóa driver khỏi bộ nhớ context
                return "Đã đóng trình duyệt trong phiên làm việc hiện tại thành công."
            except Exception as e:
                return f"Lỗi khi cố gắng đóng driver: {str(e)}"

        # TRƯỜNG HỢP 2: Không tìm thấy driver trong context (Do chạy nút lẻ hoặc Chrome bị mồ côi từ lần trước)
        else:
            print("\n⚠️ Không tìm thấy driver trong context. Đang tiến hành cưỡng chế tắt toàn bộ tiến trình Chrome chạy ngầm trên Windows...")
            try:
                # >nul 2>&1 là mẹo để ẩn các thông báo rác của Windows CMD, giúp Terminal của bạn sạch sẽ
                os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
                os.system("taskkill /f /im chrome.exe >nul 2>&1")
                
                return "Không có driver trong phiên hiện tại. Đã quét sạch và cưỡng chế tắt toàn bộ tiến trình Chrome/ChromeDriver chạy ngầm trên hệ thống!"
                
            except Exception as os_err:
                return f"Gặp lỗi khi thực hiện lệnh cưỡng chế tắt tiến trình: {str(os_err)}"