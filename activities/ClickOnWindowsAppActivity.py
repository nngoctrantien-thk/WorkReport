import time
from activities.BaseActivity import BaseActivity

try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None


class ClickOnWindowsAppActivity(BaseActivity):

    NAME = "ClickOnWindowsAppActivity"
    DESCRIPTION = """
    Click (nhấp chuột) vào một phần tử (Nút, Tab, Menu, Checkbox...) trên giao diện ứng dụng Windows Desktop.
    Sử dụng thư viện pywinauto (UIA backend) để tương tác trực tiếp với phần tử của hệ điều hành.
    """

    PARAMETERS = {
        "window_title": {
            "type": "string",
            "description": "Tiêu đề của cửa sổ ứng dụng cần tương tác (Ví dụ: 'Notepad', 'Calculator'). Hỗ trợ tìm kiếm theo tên gần đúng.",
            "required": True
        },
        "auto_id": {
            "type": "string",
            "description": "AutomationID của phần tử cần click (Dùng Inspect.exe hoặc Accessibility Insights để lấy - Khuyến khích dùng vì độ chính xác tuyệt đối).",
            "required": False
        },
        "control_title": {
            "type": "string",
            "description": "Tiêu đề văn bản hiển thị trên phần tử (Ví dụ: 'Save', 'Đăng nhập', 'Close').",
            "required": False
        },
        "control_type": {
            "type": "string",
            "description": "Loại phần tử cần tương tác (Ví dụ: 'Button', 'TabItem', 'CheckBox', 'MenuItem').",
            "required": False
        }
    }

    EXAMPLES = [
        "Click vào nút có title 'Đăng nhập' trên app 'Phần mềm Kế Toán'",
        "Nhấp vào nút Button có auto_id 'num5Button' của ứng dụng 'Calculator'",
        "Click chọn CheckBox có auto_id 'chkRememberMe' trên cửa sổ 'Login'"
    ]

    @staticmethod
    def execute(context=None, window_title=None, auto_id=None, control_title=None, control_type=None, **kwargs):
        if Desktop is None:
            return "❌ Thất bại: Hệ thống chưa cài đặt thư viện 'pywinauto'. Vui lòng chạy lệnh 'pip install pywinauto'."

        if not window_title:
            return "❌ Thất bại: Thiếu tham số 'window_title' để xác định cửa sổ ứng dụng."

        if not any([auto_id, control_title, control_type]):
            return "❌ Thất bại: Bạn phải cung cấp ít nhất một tham số để định vị phần tử (`auto_id`, `control_title` hoặc `control_type`)."

        try:
            # 1. Tìm kiếm và kết nối tới cửa sổ ứng dụng Desktop (Hỗ trợ regex tìm tên gần đúng)
            app_desktop = Desktop(backend="uia")
            window = app_desktop.window(title_re=f".*{window_title}.*")
            
            if not window.exists(timeout=3):
                return f"❌ Không tìm thấy cửa sổ ứng dụng nào khớp với tên: '{window_title}'"

            # Đưa ứng dụng lên hàng đầu màn hình và tập trung (Focus) vào nó
            window.set_focus()
            time.sleep(0.2)

            # 2. Xây dựng bộ lọc để tìm phần tử con bên trong ứng dụng
            search_criteria = {}
            if auto_id:
                search_criteria["auto_id"] = auto_id
            if control_title:
                search_criteria["title"] = control_title
            if control_type:
                search_criteria["control_type"] = control_type

            # Tìm kiếm phần tử con
            element = window.child_window(**search_criteria)
            if not element.exists(timeout=3):
                return f"❌ Không tìm thấy phần tử trong ứng dụng '{window_title}' với bộ lọc đã cho: {search_criteria}"

            # 3. Thực hiện hành động Click chuột vật lý (click_input an toàn hơn click thông thường)
            element.click_input()
            
            return f"🎯 Đã click thành công vào phần tử trong ứng dụng '{window_title}'."

        except Exception as e:
            return f"❌ Lỗi khi tương tác với ứng dụng Windows: {str(e)}"