import os
from activities.BaseActivity import BaseActivity

class ScreenshotActivity(BaseActivity):

    @staticmethod
    def execute(context=None, filename="screenshot.png"):
        # 1. Lấy driver từ context do OpenBrowserActivity truyền lại
        if context and "driver" in context:
            driver = context["driver"]
        else:
            return "Lỗi: Không tìm thấy trình duyệt đang hoạt động trong hệ thống để chụp ảnh."

        try:
            # 2. Thực hiện chụp ảnh màn hình
            # Bạn có thể lưu vào thư mục download hoặc thư mục dự án hiện tại
            driver.save_screenshot(filename)
            
            # (Tùy chọn) Lưu đường dẫn ảnh vào context để các Activity phía sau nếu cần gửi ảnh đi thì dùng
            context["screenshot_path"] = filename 
            
            return f"Chụp ảnh màn hình thành công, đã lưu tại: {filename}"
            
        except Exception as e:
            return f"Lỗi trong quá trình chụp ảnh màn hình: {str(e)}"