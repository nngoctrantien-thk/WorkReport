import os
import subprocess
import shlex
import shutil
import winreg
from activities.BaseActivity import BaseActivity
from service.Logger import get_logger

logger = get_logger(__name__)


class OpenWindowsAppActivity(BaseActivity):

    NAME = "OpenWindowsAppActivity"
    DESCRIPTION = """
    Khởi chạy một ứng dụng bất kỳ trên hệ thống Windows. 
    Nếu không phải app mặc định, hệ thống sẽ tự động dò tìm đường dẫn tuyệt đối để khởi chạy.
    """

    PARAMETERS = {
        "app_path": {
            "type": "string",
            "description": "Tên viết tắt (notepad, chrome, excel) hoặc đường dẫn đầy đủ đến file .exe của phần mềm.",
            "required": True
        },
        "args": {
            "type": "string",
            "description": "Các tham số hoặc đường dẫn file cần mở kèm theo ứng dụng (Ví dụ: 'C:\\test.txt').",
            "required": False,
            "default": None
        }
    }

    EXAMPLES = [
        "Mở ứng dụng notepad",
        "Bật trình duyệt chrome",
        "Chạy phần mềm vscode",
        "Mở phần mềm excel"
    ]

    @staticmethod
    def _auto_find_executable(app_name):
        """
        Thuật toán dò tìm thông minh đường dẫn thực thi (.exe) của ứng dụng trên Windows.
        """
        app_name = app_name.strip()
        
        # Chuẩn hóa đuôi tệp tin
        exe_name = app_name if app_name.lower().endswith('.exe') else f"{app_name}.exe"
        pure_name = app_name[:-4] if app_name.lower().endswith('.exe') else app_name

        # --- BƯỚC 1: TRA CỨU WINDOWS REGISTRY (APP PATHS) - NHANH & CHÍNH XÁC NHẤT ---
        registry_roots = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
            r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\App Paths"
        ]
        for base_path in registry_roots:
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    key_path = f"{base_path}\\{exe_name}"
                    with winreg.OpenKey(hive, key_path) as key:
                        # Giá trị mặc định (Default) của Key này thường là đường dẫn chuẩn tới file exe
                        val, _ = winreg.QueryValueEx(key, "")
                        resolved_path = str(val).strip('"').strip()
                        if resolved_path and os.path.exists(resolved_path):
                            return resolved_path
                except FileNotFoundError:
                    continue

        # --- BƯỚC 2: QUÉT NHANH CÁC THƯ MỤC CÀI ĐẶT PHỔ BIẾN (GIỚI HẠN ĐỘ SÂU CHỐNG TREO) ---
        common_folders = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
            os.path.expandvars(r"%APPDATA%")
        ]

        for root in common_folders:
            if not root or not os.path.exists(root):
                continue
            try:
                # Quét cấp 1: Tìm các thư mục mang tên ứng dụng (Ví dụ: C:\Program Files\Google)
                for item in os.listdir(root):
                    item_path = os.path.join(root, item)
                    if os.path.isdir(item_path):
                        # Thử tìm trực tiếp file exe ở ngay thư mục này
                        direct_exe = os.path.join(item_path, exe_name)
                        if os.path.exists(direct_exe):
                            return direct_exe
                        
                        # Thử quét thêm 1 cấp thư mục con (Ví dụ: Google\Chrome\Application\chrome.exe)
                        if item.lower() in [pure_name.lower(), "google", "microsoft", "programs"]:
                            for sub_item in os.listdir(item_path):
                                sub_item_path = os.path.join(item_path, sub_item)
                                if os.path.isdir(sub_item_path):
                                    deep_exe = os.path.join(sub_item_path, exe_name)
                                    if os.path.exists(deep_exe):
                                        return deep_exe
            except Exception:
                continue

        return None

    @staticmethod
    def execute(context=None, app_path=None, args=None, **kwargs):
        if not app_path:
            return "❌ Thất bại: Vui lòng cung cấp tên hoặc đường dẫn của ứng dụng cần mở."

        raw_app_path = str(app_path).strip()
        final_executable = None

        # =================================================================
        # CHIẾN LƯỢC XÁC ĐỊNH ĐƯỜNG DẪN ỨNG DỤNG
        # =================================================================
        # 1. Nếu người dùng truyền vào một đường dẫn tuyệt đối có thật
        if os.path.isabs(raw_app_path) and os.path.exists(raw_app_path):
            final_executable = raw_app_path
            
        # 2. Nếu là các lệnh hệ thống mặc định ăn theo biến môi trường PATH (notepad, calc, cmd...)
        elif shutil.which(raw_app_path):
            final_executable = shutil.which(raw_app_path)
            
        # 3. Kích hoạt radar tự động dò tìm thông minh cho các ứng dụng cài thêm
        else:
            logger.info(f"[OpenApp] Tên ứng dụng '{raw_app_path}' không nằm trong PATH. Kích hoạt radar tự dò đường...")
            found_path = OpenWindowsAppActivity._auto_find_executable(raw_app_path)
            if found_path:
                final_executable = found_path
                logger.info(f"[OpenApp] Radar đã tìm thấy vị trí cài đặt thật: {final_executable}")

        # Nếu quét sạch sành sanh mà không ông nào nhận diện được
        if not final_executable:
            return (
                f"❌ Thất bại: Không thể tìm thấy ứng dụng '{raw_app_path}' trên máy tính.\n"
                f"💡 Gợi ý: Hãy kiểm tra lại tên ứng dụng hoặc truyền đầy đủ đường dẫn `.exe` nếu đây là phần mềm portable."
            )

        # =================================================================
        # TIẾN HÀNH KHỞI CHẠY TIẾN TRÌNH
        # =================================================================
        command = [final_executable]
        if args:
            try:
                command.extend(shlex.split(str(args)))
            except Exception:
                command.append(str(args))

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Lưu lại trạng thái tiến trình vào RAM dùng chung (Context)
            if context is not None:
                context["last_opened_app_pid"] = process.pid
                context["last_opened_app_name"] = os.path.basename(final_executable)

            return (
                f"🚀 KHỞI CHẠY ỨNG DỤNG THÀNH CÔNG\n"
                f"📂 Phần mềm: {os.path.basename(final_executable)}\n"
                f"📍 Vị trí thật: `{final_executable}`\n"
                f"🆔 Mã tiến trình (PID): {process.pid}"
            )

        except Exception as e:
            logger.error(f"[OpenApp] Lỗi hệ thống khi khởi chạy tệp {final_executable}: {str(e)}")
            return f"❌ Gặp lỗi hệ thống khi cố gắng khởi chạy ứng dụng: {str(e)}"