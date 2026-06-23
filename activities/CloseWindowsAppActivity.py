import subprocess
from activities.BaseActivity import BaseActivity
from service.Logger import get_logger

logger = get_logger(__name__)


class CloseWindowsAppActivity(BaseActivity):

    NAME = "CloseWindowsAppActivity"
    DESCRIPTION = """
    Kiểm tra xem một ứng dụng Windows có đang mở hay không. 
    Nếu ứng dụng đang mở, hệ thống sẽ tiến hành đóng/tắt hoàn toàn tiến trình đó.
    """

    PARAMETERS = {
        "pid": {
            "type": "integer",
            "description": "Mã tiến trình (PID) của ứng dụng cần kiểm tra và đóng.",
            "required": False,
            "default": None
        },
        "app_name": {
            "type": "string",
            "description": "Tên file thực thi của ứng dụng cần kiểm tra (Ví dụ: 'notepad', 'chrome').",
            "required": False,
            "default": None
        }
    }

    EXAMPLES = [
        "Kiểm tra xem app có mở không rồi mới đóng",
        "Kiểm tra và tắt ứng dụng chrome",
        "Đóng phần mềm notepad nếu nó đang chạy",
        "Tắt app vừa mở nếu còn chạy"
    ]

    @staticmethod
    def _is_process_running(pid=None, app_name=None):
        """
        BƯỚC CHÈN THÊM: Sử dụng lệnh tasklist để kiểm tra thời gian thực 
        xem ứng dụng có đang hiển thị/chạy trên Windows không.
        """
        if pid:
            # /FI là bộ lọc điều kiện, /NH là ẩn dòng tiêu đề (No Headers)
            command_check = ["tasklist", "/FI", f"PID eq {pid}", "/NH"]
        elif app_name:
            command_check = ["tasklist", "/FI", f"IMAGENAME eq {app_name}", "/NH"]
        else:
            return False

        try:
            result = subprocess.run(
                command_check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW # Chạy ẩn danh không nháy khung đen
            )
            output = result.stdout.lower()
            
            # Nếu trong danh sách trả về có chứa đúng số PID hoặc tên tiến trình thực thi
            if pid and str(pid) in output:
                return True
            if app_name and app_name.lower() in output:
                return True
        except Exception as e:
            logger.error(f"[CloseApp] Lỗi khi quét danh sách tasklist Windows: {str(e)}")
            
        return False

    @staticmethod
    def execute(context=None, pid=None, app_name=None, **kwargs):
        target_pid = pid
        target_name = app_name

        # 1. Tự động bốc thông tin từ RAM Context nếu người dùng ra lệnh chung chung ("Tắt app vừa mở")
        if not target_pid and not target_name and context:
            target_pid = context.get("last_opened_app_pid")
            target_name = context.get("last_opened_app_name")
            logger.info(f"[CloseApp] Tự động lấy từ bộ nhớ luồng: PID={target_pid}, Name={target_name}")

        # Chuẩn hóa tên tiến trình luôn có đuôi .exe (Ví dụ: chrome -> chrome.exe)
        if target_name and not target_pid:
            target_name = str(target_name).strip()
            if not target_name.lower().endswith(".exe"):
                target_name = f"{target_name}.exe"

        if target_pid:
            display_target = f"Mã tiến trình (PID): {target_pid}"
        elif target_name:
            display_target = f"Ứng dụng: {target_name}"
        else:
            return "⚠️ Thất bại: Không xác định được ứng dụng nào để kiểm tra (Tham số trống và bộ nhớ tạm trống)."

        # =================================================================
        # BƯỚC 1: KIỂM TRA TRẠNG THÁI (PRE-CHECK)
        # =================================================================
        is_running = CloseWindowsAppActivity._is_process_running(pid=target_pid, app_name=target_name)
        
        # NẾU KHÔNG MỞ -> Dừng luồng ngay tại đây và thông báo cho người dùng
        if not is_running:
            return (
                f"🔍 KẾT QUẢ KIỂM TRA HỆ THỐNG\n"
                f"📌 Đối tượng: {display_target}\n"
                f"ℹ️ Trạng thái: Hiện tại **KHÔNG CHẠY** (Đang đóng).\n"
                f"✨ Hệ thống tự động bỏ qua lệnh tắt ứng dụng này!"
            )

        # =================================================================
        # BƯỚC 2: TIẾN HÀNH ĐÓNG ỨNG DỤNG (Chỉ chạy khi bước 1 xác nhận ĐANG MỞ)
        # =================================================================
        command_kill = ["taskkill", "/F"]
        if target_pid:
            command_kill.extend(["/PID", str(target_pid)])
        else:
            command_kill.extend(["/IM", target_name])

        try:
            logger.info(f"[CloseApp] Ứng dụng đang mở. Kích hoạt lệnh đóng: {command_kill}")
            result = subprocess.run(
                command_kill,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                # Xóa sạch dữ liệu lưu vết cũ trong RAM Context sau khi đã xử lý xong
                if context and not pid and not app_name:
                    context.pop("last_opened_app_pid", None)
                    context.pop("last_opened_app_name", None)

                return (
                    f"💀 ĐÃ ĐÓNG ỨNG DỤNG THÀNH CÔNG\n"
                    f"🎯 Đối tượng: {display_target}\n"
                    f"🔍 Trạng thái pre-check: Phát hiện ứng dụng ĐANG MỞ\n"
                    f"✨ Tiến trình đã được chấm dứt an toàn!"
                )
            else:
                return f"❌ Thất bại khi cố gắng đóng ứng dụng: {result.stderr.strip()}"

        except Exception as e:
            logger.error(f"[CloseApp] Lỗi hệ thống khi thực thi taskkill: {str(e)}")
            return f"❌ Lỗi hệ thống khi cố đóng ứng dụng: {str(e)}"