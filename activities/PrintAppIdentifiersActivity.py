import contextlib
import io
import os
import time
import re
from activities.BaseActivity import BaseActivity

try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None


class PrintAppIdentifiersActivity(BaseActivity):

    NAME = "PrintAppIdentifiersActivity"
    DESCRIPTION = """
    Quét cấu trúc cây giao diện (UI Tree) của ứng dụng Windows và tự động xuất ra file .txt 
    để gửi dưới dạng Document qua Telegram, tránh lỗi quá tải dung lượng tin nhắn (Entity Too Large).
    """

    PARAMETERS = {
        "window_title": {
            "type": "string",
            "description": "Tiêu đề của cửa sổ ứng dụng cần quét.",
            "required": True
        }
    }

    EXAMPLES = [
        "In ra toàn bộ mã ID của ứng dụng Postman thành file",
        "Quét cấu trúc giao diện của cửa sổ 'Phần mềm Kế Toán'"
    ]

    @staticmethod
    def execute(context=None, window_title=None, **kwargs):
        if Desktop is None:
            return "❌ Thất bại: Hệ thống chưa cài đặt thư viện 'pywinauto'."

        if not window_title:
            return "❌ Thất bại: Thiếu tham số 'window_title' để xác định ứng dụng."

        try:
            # 1. Kết nối tới ứng dụng
            app_desktop = Desktop(backend="uia")
            window = app_desktop.window(title_re=f".*{window_title}.*")
            
            if not window.exists(timeout=3):
                return f"❌ Không tìm thấy cửa sổ ứng dụng nào khớp với tên: '{window_title}'"

            window.set_focus()
            time.sleep(0.3)

            # 2. Hứng dữ liệu UI Tree từ pywinauto
            string_buffer = io.StringIO()
            with contextlib.redirect_stdout(string_buffer):
                window.print_control_identifiers()
            
            ui_tree_output = string_buffer.getvalue()

            # 3. CHUYỂN ĐỔI THÀNH FILE .TXT AN TOÀN
            # Làm sạch tên file (bỏ ký tự đặc biệt nếu có)
            safe_title = re.sub(r'[\\/*?:"<>| ]', '_', window_title)
            file_name = f"ui_tree_{safe_title}.txt"
            file_path = os.path.join(os.getcwd(), file_name)

            # Ghi dữ liệu vào file mã hóa UTF-8 để không lỗi font tiếng Việt
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ui_tree_output)

            # 4. ĐÁNH DẤU VÀO CONTEXT ĐỂ TELEGRAM BOT BIẾT ĐƯỜNG UPLOAD FILE
            if context is not None:
                context["telegram_send_as_file"] = True  # Cờ đánh dấu: Cần gửi dạng File
                context["telegram_file_path"] = file_path # Đường dẫn file để bot bốc đi gửi

            return f"📁 Đã quét xong ứng dụng '{window_title}'. Do cấu trúc quá lớn, hệ thống đã tự động tạo file và chuẩn bị upload lên Telegram cho bạn."

        except Exception as e:
            return f"❌ Lỗi khi quét cấu trúc và xuất file: {str(e)}"