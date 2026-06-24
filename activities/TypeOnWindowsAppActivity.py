import time
from activities.BaseActivity import BaseActivity

try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None


class TypeOnWindowsAppActivity(BaseActivity):

    NAME = "TypeOnWindowsAppActivity"
    DESCRIPTION = """
    Nhập dữ liệu văn bản vào ô nhập liệu (Edit, Document, TextBox) của một ứng dụng Windows Desktop.
    Hỗ trợ tính năng tự động xóa sạch dữ liệu cũ trong ô trước khi gõ văn bản mới.
    """

    PARAMETERS = {
        "window_title": {
            "type": "string",
            "description": "Tiêu đề của cửa sổ ứng dụng (Ví dụ: 'Untitled - Notepad').",
            "required": True
        },
        "text": {
            "type": "string",
            "description": "Nội dung chuỗi văn bản cần nhập vào ứng dụng.",
            "required": True
        },
        "auto_id": {
            "type": "string",
            "description": "AutomationID của ô nhập liệu.",
            "required": False
        },
        "control_title": {
            "type": "string",
            "description": "Tiêu đề hiển thị hoặc Name của ô nhập liệu.",
            "required": False
        },
        "control_type": {
            "type": "string",
            "description": "Loại phần tử nhập liệu (Mặc định thường là 'Edit' hoặc 'Document').",
            "required": False,
            "default": "Edit"
        },
        "clear_before": {
            "type": "boolean",
            "description": "Xóa toàn bộ chữ cũ đang có sẵn trong ô trước khi nhập mới hay không.",
            "required": False,
            "default": True
        }
    }

    EXAMPLES = [
        "Nhập nội dung 'Xin chào Việt Nam' vào ứng dụng 'Notepad'",
        "Điền mã số thuế vào ô nhập liệu có auto_id 'txtTaxCode' trên ứng dụng 'Hỗ trợ kê khai'",
        "Nhập 'admin' vào ô Edit của cửa sổ 'Đăng nhập hệ thống'"
    ]

    @staticmethod
    def execute(context=None, window_title=None, text="", auto_id=None, control_title=None, control_type="Edit", clear_before=True, **kwargs):
        if Desktop is None:
            return "❌ Thất bại: Hệ thống chưa cài đặt thư viện 'pywinauto'."

        if not window_title:
            return "❌ Thất bại: Thiếu tham số 'window_title'."

        try:
            # 1. Tìm và kết nối cửa sổ ứng dụng
            app_desktop = Desktop(backend="uia")
            window = app_desktop.window(title_re=f".*{window_title}.*")
            
            if not window.exists(timeout=3):
                return f"❌ Không tìm thấy cửa sổ ứng dụng: '{window_title}'"

            window.set_focus()
            time.sleep(0.2)

            # 2. Định vị ô nhập liệu con
            search_criteria = {}
            if auto_id:
                search_criteria["auto_id"] = auto_id
            if control_title:
                search_criteria["title"] = control_title
            if control_type:
                search_criteria["control_type"] = control_type

            element = window.child_window(**search_criteria)
            if not element.exists(timeout=3):
                return f"❌ Không tìm thấy ô nhập liệu trong ứng dụng với bộ lọc: {search_criteria}"

            # Kích hoạt phần tử để sẵn sàng gõ phím
            element.click_input()
            time.sleep(0.1)

            # 3. Xử lý xóa text cũ nếu có yêu cầu (Gửi tổ hợp phím Ctrl+A rồi Backspace)
            if clear_before:
                element.type_keys("^a{BACKSPACE}")
                time.sleep(0.1)

            # 4. Thực hiện gõ văn bản chuỗi mới vào (with_spaces=True giữ lại khoảng trắng nguyên bản)
            if text:
                element.type_keys(str(text), with_spaces=True)

            return f"⌨️ Đã nhập văn bản thành công vào ứng dụng '{window_title}'."

        except Exception as e:
            return f"❌ Lỗi khi thực hiện gõ phím trên ứng dụng Windows: {str(e)}"