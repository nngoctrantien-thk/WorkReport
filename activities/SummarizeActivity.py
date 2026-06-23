# import time
# from google.genai.errors import APIError
# from selenium.webdriver.common.by import By
# from config import MODELS, GEMINI_API_KEYS  # Dùng danh sách KEYS và MODELS từ config
# from activities.BaseActivity import BaseActivity
# from service.GeminiClientManager import GeminiClientManager  # Quản lý Key động


# class SummarizeActivity(BaseActivity):
    
#     # Đã BỎ dòng khởi tạo client tĩnh ở đây để tránh dùng cố định 1 key

#     @staticmethod
#     def execute(context=None, html=None, image_path=None, **kwargs):
        
#         # 1. Lấy mã HTML trực tiếp từ trình duyệt đang mở ở bước trước thông qua context
#         if context and "driver" in context:
#             driver = context["driver"]
            
#             # Chờ 3 giây để trang Redmine tải xong hoàn toàn dữ liệu chữ
#             time.sleep(3)
            
#             try:
#                 # Lấy thẻ body để cào text trang web một cách chuẩn xác nhất
#                 page_content = driver.find_element(By.TAG_NAME, "body").text 
                
#                 if not page_content.strip():
#                     return "Lỗi: Nội dung trang web trống, không có chữ để tóm tắt."
#             except Exception as sel_err:
#                 return f"Lỗi Selenium khi cào dữ liệu chữ: {str(sel_err)}"
#         else:
#             return "Lỗi: Không tìm thấy trình duyệt đang hoạt động trong hệ thống."

#         # Tạo prompt yêu cầu AI làm việc
#         prompt = f"""
# Bạn là trợ lý tóm tắt văn bản. Hãy tóm tắt nội dung chính của trang web sau đây một cách ngắn gọn, rõ ràng:

# {page_content}
# """

#         models_to_try = MODELS
        
#         # Vòng lặp lớn: Duyệt qua từng đời Model
#         for model_name in models_to_try:
            
#             # Vòng lặp nhỏ: Thử lần lượt qua số lượng API Key đang có
#             for _ in range(len(GEMINI_API_KEYS)):
#                 try:
#                     # Lấy client động theo Key đang active từ Manager
#                     client = GeminiClientManager.get_client()
                    
#                     print(f"[Summarize] Đang thử tóm tắt bằng model: {model_name}...")
#                     response = client.models.generate_content(
#                         model=model_name,
#                         contents=prompt
#                     )
                    
#                     # Nếu gọi thành công, trả kết quả về luôn và thoát hàm
#                     return response.text
                    
#                 except APIError as e:
#                     # NẾU DÍNH LỖI HẾT LƯỢT (429) Ở BƯỚC TÓM TẮT
#                     if e.code == 429:
#                         print(f"⚠️ Key hiện tại đã HẾT QUOTA (429) khi đang tóm tắt bằng {model_name}!")
                        
#                         # Kích hoạt đổi sang Key tiếp theo
#                         if GeminiClientManager.rotate_key():
#                             print("🔄 Đã đổi sang Key mới thành công cho bước tóm tắt. Đang chạy lại...")
#                             continue  # Ép vòng lặp nhỏ thử lại chính model này với Key mới
#                         else:
#                             break  # Nếu không còn key nào để đổi, thoát vòng lặp nhỏ
                            
#                     elif e.code == 503:
#                         print(f"⚠️ Model {model_name} bận (503). Đang đổi sang model dự phòng...")
#                         break  # Thoát vòng lặp nhỏ để nhảy sang model tiếp theo
#                     else:
#                         print(f"❌ Lỗi API từ Gemini ({model_name}): {str(e)}")
#                         break  # Thoát ra thử model khác
                        
#                 except Exception as e:
#                     print(f"❌ Lỗi hệ thống bất ngờ tại bước tóm tắt: {str(e)}")
#                     break

#         # Nếu chạy qua sạch sành sanh các Model và các Key mà vẫn thất bại
#         return "Lỗi nghiêm trọng: Tất cả các model và API Key dự phòng của Free Tier đều đã cạn kiệt lượt dùng trong ngày."
import time

from google.genai.errors import APIError

from activities.BaseActivity import BaseActivity

from config import MODELS
from config import GEMINI_API_KEYS

from service.GeminiClientManager import GeminiClientManager

from service.ChromeManager import ChromeManager


class SummarizeActivity(BaseActivity):

    NAME = "SummarizeActivity"

    DESCRIPTION = "Tóm tắt nội dung tab Chrome."

    PARAMETERS = {}

    @staticmethod
    def execute(context=None, **kwargs):

        manager = ChromeManager(context=context)

        page_content = manager.get_current_page_text()

        if not page_content:
            return "Không lấy được nội dung trang."

        prompt = f"""
Bạn là trợ lý AI.

Hãy tóm tắt nội dung sau thật ngắn gọn.

{page_content}
"""

        for model_name in MODELS:

            for _ in range(len(GEMINI_API_KEYS)):

                try:

                    client = GeminiClientManager.get_client()

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    return response.text

                except APIError as e:

                    if e.code == 429:

                        if GeminiClientManager.rotate_key():
                            continue

                        break

                    if e.code == 503:
                        break

                    break

                except Exception:
                    break

        return "❌ Không còn model hoặc API Key khả dụng."