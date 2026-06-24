import time
from activities.BaseActivity import BaseActivity

try:
    from pywinauto import Desktop
    from pywinauto.keyboard import send_keys
except ImportError:
    Desktop = None
    send_keys = None


class SendKeyboardActionActivity(BaseActivity):

    NAME = "SendKeyboardActionActivity"
    DESCRIPTION = """
    Kích hoạt một ứng dụng Windows lên màn hình và gửi trực tiếp các lệnh bấm phím đơn hoặc tổ hợp phím 
    (Enter, Tab, Esc, Mũi tên, Ctrl+S,...) từ tầng hệ điều hành (giống hệt bàn phím vật lý).
    Giải quyết triệt để lỗi các phần tử cứng đầu chặn hoặc nuốt phím chức năng.
    """

    PARAMETERS = {
        "window_title": {
            "type": "string",
            "description": "Tiêu đề của cửa sổ ứng dụng cần nhận phím bấm (Ví dụ: 'Postman', 'Notepad').",
            "required": True
        },
        "keys": {
            "type": "string",
            "description": "Mã phím cần bấm. Ví dụ: '{ENTER}' (phím Enter), '{TAB}' (phím Tab), '^s' (Ctrl+S), '%{F4}' (Alt+F4).",
            "required": True
        }
    }

    EXAMPLES = [
        "Nhấn phím Enter trên ứng dụng Postman",
        "Gửi lệnh bấm Tab trên cửa sổ Đăng nhập",
        "Ấn tổ hợp phím Ctrl+S vào Notepad"
    ]

    @staticmethod
    def execute(context=None, window_title=None, keys=None, **kwargs):
        if Desktop is None or send_keys is None:
            return "❌ Thất bại: Hệ thống chưa cài đặt thư viện 'pywinauto'."

        if not window_title:
            return "❌ Thất bại: Thiếu tham số 'window_title' để xác định ứng dụng mục tiêu."

        if not keys:
            return "❌ Thất bại: Thiếu tham số 'keys' để biết cần bấm phím nào."

        try:
            # 1. Tìm kiếm ứng dụng và đưa lên hàng đầu màn hình (Ưu tiên UIA -> Fallback Win32)
            app_desktop = Desktop(backend="uia")
            window = app_desktop.window(title_re=f".*{window_title}.*")
            
            if not window.exists(timeout=2):
                app_desktop = Desktop(backend="win32")
                window = app_desktop.window(title_re=f".*{window_title}.*")
                if not window.exists(timeout=1):
                    return f"❌ Không tìm thấy cửa sổ ứng dụng nào khớp với: '{window_title}'"

            # Đánh thức và Focus tối đa vào ứng dụng
            window.set_focus()
            time.sleep(0.3)  # Chờ 300ms để hệ điều hành chuyển đổi Focus hoàn toàn sang App

            # 2. Bắn tín hiệu phím bấm từ tầng driver hệ thống (Hardware Injection)
            send_keys(str(keys), with_spaces=True)
            time.sleep(0.1)

            return f"🎹 Đã gửi tín hiệu bàn phím '{keys}' trực tiếp vào ứng dụng '{window_title}' thành công."

        except Exception as e:
            return f"❌ Lỗi khi thực hiện tương tác bàn phím: {str(e)}"