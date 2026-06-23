# import os
# from activities.BaseActivity import BaseActivity

# class ScreenshotActivity(BaseActivity):

#     @staticmethod
#     def execute(context=None, filename="screenshot.png"):
#         # 1. Lấy driver từ context do OpenBrowserActivity truyền lại
#         if context and "driver" in context:
#             driver = context["driver"]
#         else:
#             return "Lỗi: Không tìm thấy trình duyệt đang hoạt động trong hệ thống để chụp ảnh."

#         try:
#             # 2. Thực hiện chụp ảnh màn hình
#             # Bạn có thể lưu vào thư mục download hoặc thư mục dự án hiện tại
#             driver.save_screenshot(filename)
            
#             # (Tùy chọn) Lưu đường dẫn ảnh vào context để các Activity phía sau nếu cần gửi ảnh đi thì dùng
#             context["screenshot_path"] = filename 
            
#             return f"Chụp ảnh màn hình thành công, đã lưu tại: {filename}"
            
#         except Exception as e:
#             return f"Lỗi trong quá trình chụp ảnh màn hình: {str(e)}"
from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class ScreenshotActivity(BaseActivity):

    NAME = "ScreenshotActivity"
    DESCRIPTION = """
    Chụp ảnh màn hình hiện tại. Tự động ưu tiên chụp trang web từ Selenium, 
    nếu trình duyệt đóng sẽ tự động chụp ứng dụng đang mở trên màn hình máy tính.
    """

    PARAMETERS = {
        "filename": {
            "type": "string",
            "description": "Tên file hoặc đường dẫn lưu ảnh (mặc định: screenshot.png).",
            "required": False,
            "default": "screenshot.png"
        }
    }

    EXAMPLES = [
        "Chụp ảnh màn hình",
        "Chụp màn hình lưu thành ảnh_kiemtra.png",
        "Chụp lại màn hình hiện tại"
    ]

    @staticmethod
    def execute(context=None, filename="screenshot.png", **kwargs):
        user_id = kwargs.get("user_id", "global")
        
        # Khởi tạo ChromeManager gánh vác hạ tầng bóc tách
        manager = ChromeManager(context=context, user_id=user_id)
        
        # Gọi hàm xử lý đa tầng thông minh từ Manager
        success, message = manager.take_screenshot(filename)
        
        # Nếu chụp thành công, lưu lại đường dẫn vào RAM chung (Context) để lệnh sau lấy gửi đi
        if success and context is not None:
            context["screenshot_path"] = filename
            
        return message