# import json
# import os
# from activities.BaseActivity import BaseActivity


# class ClearFileContentActivity(BaseActivity):

#     NAME = "ClearFileContentActivity"
#     DESCRIPTION = """
#     Xóa sạch nội dung của một file văn bản chỉ định (log, txt) hoặc xóa bộ nhớ tạm (cache) các tab Chrome.
#     Đảm bảo định dạng an toàn để các lệnh chạy sau không bị lỗi cấu trúc.
#     """

#     PARAMETERS = {
#         "file_path": {
#             "type": "string",
#             "description": "Đường dẫn tới file cần xóa. Nếu để trống, mặc định xóa file bộ nhớ tạm tab Chrome.",
#             "required": False,
#             "default": None
#         }
#     }

#     EXAMPLES = [
#         "Xóa bộ nhớ tạm tab Chrome",
#         "Clear cache tab",
#         "Xóa sạch file log.txt",
#         "Làm trống file cấu hình"
#     ]

#     @staticmethod
#     def execute(context=None, file_path=None, **kwargs):
#         user_id = kwargs.get("user_id", "global")
#         target_path = file_path
#         is_tab_cache = False

#         # =================================================================
#         # BƯỚC 1: XÁC ĐỊNH FILE CẦN XÓA
#         # =================================================================
#         if not target_path:
#             # Nếu người dùng để trống path, tự động hiểu là muốn xóa bộ nhớ tab Chrome của họ
#             target_path = f"cache_tabs_{user_id}.json"
#             is_tab_cache = True

#         # Kiểm tra xem file thực tế có tồn tại trên máy không
#         if not os.path.exists(target_path):
#             return f"❌ File '{target_path}' không tồn tại trên hệ thống để tiến hành dọn dẹp."

#         # =================================================================
#         # BƯỚC 2: TIẾN HÀNH LÀM TRỐNG FILE AN TOÀN
#         # =================================================================
#         try:
#             # Mở file ở chế độ "w" (write) để ghi đè làm trống nội dung
#             with open(target_path, "w", encoding="utf-8") as f:
#                 # MẸO AN TOÀN: Nếu là file JSON cache, phải ghi mảng rỗng [] 
#                 # để lệnh json.load() ở các activity khác đọc không bị crash lỗi cấu trúc
#                 if is_tab_cache or target_path.lower().endswith(".json"):
#                     json.dump([], f)
#                 else:
#                     # Nếu là file text hoặc log thông thường, xóa trắng hoàn toàn
#                     f.write("")
                    
#             print(f"[ClearFile] Đã xóa sạch nội dung file thành công: {target_path}")
            
#         except Exception as e:
#             return f"❌ Gặp lỗi hệ thống khi đang xóa nội dung file: {str(e)}"

#         # =================================================================
#         # BƯỚC 3: ĐỒNG BỘ HÓA BỘ NHỚ RAM (CONTEXT)
#         # =================================================================
#         # Nếu đang xóa cache tab Chrome, tiện tay làm sạch luôn biến trong RAM hiện tại
#         if is_tab_cache and context is not None:
#             if "chrome_tabs" in context:
#                 context["chrome_tabs"] = []
#                 print("[ClearFile] Đã đồng bộ làm trống mảng chrome_tabs trong context.")

#         # =================================================================
#         # BƯỚC 4: TRẢ VỀ THÔNG BÁO (Bypass bộ lọc _short bằng dấu \\n)
#         # =================================================================
#         output_message = (
#             f"🧹 DỌN DẸP NỘI DUNG FILE THÀNH CÔNG\n"
#             f"📂 File đã xử lý: {target_path}\n"
#             f"----------------------------------------\n"
#             f"✨ Toàn bộ nội dung bên trong đã được làm trống an toàn và sẵn sàng cho các phiên làm việc tiếp theo."
#         )
#         return output_message
import os
from pathlib import Path
from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager
from service.CacheManager import CacheManager


class ClearFileContentActivity(BaseActivity):

    NAME = "ClearFileContentActivity"
    DESCRIPTION = """
    Xóa sạch nội dung của một file văn bản chỉ định (log, txt) hoặc xóa bộ nhớ tạm (cache) các tab Chrome.
    Đảm bảo định dạng an toàn để các lệnh chạy sau không bị lỗi cấu trúc.
    """

    PARAMETERS = {
        "file_path": {
            "type": "string",
            "description": "Đường dẫn tới file cần xóa. Nếu để trống, mặc định xóa file bộ nhớ tạm tab Chrome.",
            "required": False,
            "default": None
        }
    }

    EXAMPLES = [
        "Xóa bộ nhớ tạm tab Chrome",
        "Clear cache tab",
        "Xóa sạch file log.txt",
        "Làm trống file cấu hình"
    ]

    @staticmethod
    def execute(context=None, file_path=None, **kwargs):
        user_id = kwargs.get("user_id", "global")
        
        # Khởi tạo ChromeManager để tận dụng các hàm quản lý cache/context tập trung
        manager = ChromeManager(context=context, user_id=user_id)
        
        # =================================================================
        # TRƯỜNG HỢP 1: XÓA CACHE TAB CHROME (Mặc định khi file_path trống)
        # =================================================================
        if not file_path:
            # Tự động lấy đường dẫn chuẩn từ FileUtils qua ChromeManager (cache/tabs_global.json)
            target_path = manager.cache_path(user_id)
            
            if not Path(target_path).exists():
                return f"❌ Cảnh báo: File cache '{target_path}' hiện không tồn tại để tiến hành dọn dẹp."
            
            try:
                # 1. Gọi Manager dọn dẹp file JSON cache về mảng rỗng [] an toàn
                manager.clear_cache(user_id)
                
                # 2. Tiện tay đồng bộ làm sạch luôn bộ nhớ RAM (Context) tránh lệch dữ liệu
                ChromeManager.save_context(context, [])
                
            except Exception as e:
                return f"❌ Gặp lỗi khi xóa bộ nhớ tạm tab Chrome: {str(e)}"
        
        # =================================================================
        # TRƯỜNG HỢP 2: XÓA CÁC FILE ĐƯỢC CHỈ ĐỊNH CỤ THỂ (Dùng CacheManager)
        # =================================================================
        else:
            target_path = file_path
            if not os.path.exists(target_path):
                return f"❌ File '{target_path}' không tồn tại trên hệ thống để tiến hành dọn dẹp."
            
            try:
                # Tận dụng các hàm clear chuyên dụng đã viết sẵn trong CacheManager
                if str(target_path).lower().endswith(".json"):
                    # Ghi đè [] để không bị lỗi cú pháp khi nạp json ở các luồng sau
                    CacheManager.clear_json(target_path)
                else:
                    # Ghi đè chuỗi rỗng "" cho file log/text thông thường
                    CacheManager.clear_text(target_path)
            except Exception as e:
                return f"❌ Gặp lỗi hệ thống khi đang xóa nội dung file: {str(e)}"

        # =================================================================
        # ĐÓNG GÓI KẾT QUẢ TRẢ VỀ
        # =================================================================
        output_message = (
            f"🧹 DỌN DẸP NỘI DUNG FILE THÀNH CÔNG\n"
            f"📂 File đã xử lý: {target_path}\n"
            f"----------------------------------------\n"
            f"✨ Toàn bộ nội dung bên trong đã được làm trống an toàn và sẵn sàng cho các phiên làm việc tiếp theo."
        )
        return output_message