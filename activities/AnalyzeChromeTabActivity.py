# import http.client
# import json
# import os
# import time
# import win32clipboard  # Thư viện thao tác clipboard hệ thống
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from activities.BaseActivity import BaseActivity
# from config import MODELS, GEMINI_API_KEYS
# from service.GeminiClientManager import GeminiClientManager
# from google.genai.errors import APIError

# # Nhập thư viện AI của Google
# try:
#     import google.generativeai as genai
#     # Điền API Key của bạn vào đây hoặc thiết lập trong biến môi trường GEMINI_API_KEY
#     if os.environ.get("GEMINI_API_KEY"):
#         genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
# except ImportError:
#     genai = None

# # Nhập thư viện UI Automation phòng trường hợp chạy không debug
# try:
#     from pywinauto import Desktop
# except ImportError:
#     Desktop = None


# class AnalyzeChromeTabActivity(BaseActivity):

#     NAME = "AnalyzeChromeTabActivity"
#     DESCRIPTION = """
#     Trích xuất toàn bộ nội dung chữ của một tab Chrome (theo index hoặc từ khóa)
#     và sử dụng Gemini AI để phân tích, tóm tắt lại nội dung chính.
#     """

#     PARAMETERS = {
#         "index": {
#             "type": "integer",
#             "description": "Số thứ tự của tab cần phân tích (1, 2, 3...).",
#             "required": False,
#             "default": None
#         },
#         "keyword": {
#             "type": "string",
#             "description": "Từ khóa trong tiêu đề để tìm tab cần phân tích.",
#             "required": False,
#             "default": None
#         },
#         "remote_port": {
#             "type": "integer",
#             "description": "Cổng Debug của Chrome",
#             "required": False,
#             "default": 9222
#         }
#     }

#     EXAMPLES = [
#         "Phân tích tab số 3",
#         "Tóm tắt nội dung tab google docs",
#         "Đọc nội dung tab index=5",
#         "Xem tab số 2 viết về cái gì"
#     ]

#     @staticmethod
#     def execute(context=None, index=None, keyword=None, remote_port=9222, **kwargs):
#         user_id = kwargs.get("user_id", "global")
#         file_cache_name = f"cache_tabs_{user_id}.json"
#         saved_tabs = []

#         # =================================================================
#         # BƯỚC 1: ĐỌC LẠI LỊCH SỬ DANH SÁCH TAB
#         # =================================================================
#         if context and context.get("chrome_tabs"):
#             saved_tabs = context["chrome_tabs"]
#         elif os.path.exists(file_cache_name):
#             try:
#                 with open(file_cache_name, "r", encoding="utf-8") as f:
#                     saved_tabs = json.load(f)
#             except Exception as e:
#                 return f"❌ Không thể đọc bộ nhớ tab cũ: {str(e)}"

#         if not saved_tabs:
#             return "❌ Chưa có dữ liệu tab. Vui lòng chạy lệnh kiểm tra danh sách tab trước."

#         # =================================================================
#         # BƯỚC 2: XÁC ĐỊNH TAB CẦN PHÂN TÍCH
#         # =================================================================
#         target_tab = None
#         if index is not None:
#             target_idx = int(index) - 1
#             if 0 <= target_idx < len(saved_tabs):
#                 target_tab = saved_tabs[target_idx]
#             else:
#                 return f"❌ Vị trí {index} không hợp lệ. Chỉ có từ 1 đến {len(saved_tabs)}."
#         elif keyword:
#             kw = str(keyword).lower().strip()
#             for tab in saved_tabs:
#                 if kw in str(tab.get("title", "")).lower() or kw in str(tab.get("url", "")).lower():
#                     target_tab = tab
#                     break
#             if not target_tab:
#                 return f"❌ Không tìm thấy tab nào chứa từ khóa: '{keyword}'"
#         else:
#             return "❌ Vui lòng truyền tham số 'index' (số thứ tự) hoặc 'keyword' để chọn tab cần phân tích."

#         tab_title = target_tab.get("title", "Không rõ tiêu đề")
#         tab_url = target_tab.get("url", "")
#         source = target_tab.get("source", "")
#         handle = target_tab.get("handle")
        
#         web_text_content = ""

#         # =================================================================
#         # BƯỚC 3: TRÍCH XUẤT CHỮ (TEXT CONTENT) TỪ TRANG WEB
#         # =================================================================
        
#         # --- Cách A: Nếu có kết nối Driver Selenium hoặc Cổng Debug ---
#         if (source in ["chrome_api", "selenium"]) and handle:
#             driver = context.get("driver") if context else None
#             is_temp_driver = False
            
#             try:
#                 if not driver:
#                     # Nếu chưa có sẵn driver trong context, khởi tạo nhanh qua cổng debug
#                     options = Options()
#                     options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
#                     driver = webdriver.Chrome(options=options)
#                     is_temp_driver = True

#                 # Chuyển hướng selenium sang tab mục tiêu
#                 driver.switch_to.window(handle)
#                 # Lấy toàn bộ nội dung text hiển thị trên body của trang web
#                 web_text_content = driver.find_element(By.TAG_NAME, "body").text
                
#                 if is_temp_driver:
#                     driver.quit() # Đóng driver tạm nếu tự tạo ra
#             except Exception as e:
#                 print(f"[AnalyzeTab] Lỗi bóc dữ liệu bằng Selenium: {str(e)}")

#         # --- Cách B: Nếu quét bằng UI Automation (Không có Debug) ---
#         if not web_text_content and Desktop is not None:
#             try:
#                 windows = Desktop(backend="uia").windows(class_name="Chrome_WidgetWin_1")
#                 for win in windows:
#                     tab_items = win.descendants(control_type="TabItem")
#                     for tab in tab_items:
#                         if tab.window_text() == tab_title:
#                             win.set_focus()
#                             tab.click_input()
#                             time.sleep(0.5)
#                             win.click_input()
#                             time.sleep(0.3)
#                             win.type_keys('^a^c')
#                             time.sleep(0.5)
                            
#                             win32clipboard.OpenClipboard()
#                             web_text_content = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
#                             win32clipboard.CloseClipboard()
#                             break
#                     if web_text_content:
#                         break
#             except Exception as e:
#                 print(f"[AnalyzeTab] Lỗi cào text bằng UI Automation: {str(e)}")

#         # Kiểm tra xem có lấy được chữ nào không
#         if not web_text_content or len(web_text_content.strip()) < 10:
#             return f"❌ Không thể trích xuất nội dung văn bản từ tab:\n📌 *{tab_title}*\n(Có thể trang web trống hoặc chưa tải xong)."

#         # Cắt bớt dữ liệu thô nếu quá dài trước khi gửi lên AI (Tránh tràn token)
#         web_text_content = web_text_content[:8000]

#         # =================================================================
#         # BƯỚC 4: GỬI NỘI DUNG QUA AI ĐỂ PHÂN TÍCH VÀ TÓM TẮT
#         # =================================================================
#         if genai is None:
#             return f"⚠️ Đã lấy được dữ liệu nhưng thiếu thư viện AI.\n\n📄 **Nội dung thô (Đoạn đầu):**\n{web_text_content[:500]}..."

#         try:
#             # =================================================================
#             # BƯỚC 4: GỬI NỘI DUNG QUA AI ĐỂ PHÂN TÍCH VÀ TÓM TẮT 
#             # =================================================================
#             prompt = f"""
#             Bạn là một trợ lý AI phân tích nội dung trang web chuyên nghiệp.
#             Hãy đọc và phân tích nội dung văn bản thô được trích xuất từ trang web dưới đây.
            
#             Thông tin trang web:
#             - Tiêu đề: {tab_title}
#             - Đường dẫn: {tab_url}
            
#             Nội dung văn bản thô:
#             \"\"\"
#             {web_text_content}
#             \"\"\"
            
#             Yêu cầu phản hồi:
#             1. Tóm tắt ngắn gọn trang web này nói về cái gì (2-3 câu).
#             2. Liệt kê từ 3 đến 5 ý chính quan trọng nhất dưới dạng gạch đầu dòng.
#             3. Đưa ra đánh giá nhanh hoặc phân loại thể loại của trang web này (Ví dụ: Tin tức, Công việc, Tài liệu kỹ thuật, Giải trí...).
            
#             Viết câu trả lời bằng tiếng Việt, rõ ràng, gãy gọn, không sử dụng các ký tự markdown nguy hiểm bọc ngoài tiêu đề.
#             """

#             ai_analysis = None

#             # VÒNG LẶP NGOÀI: Duyệt qua từng tài khoản API Key đang cấu hình
#             for _ in range(len(GEMINI_API_KEYS)):
#                 try:
#                     # Lấy client động theo Key đang kích hoạt hiện tại
#                     client = GeminiClientManager.get_client()
                    
#                     # VÒNG LẶP TRONG: Quét hết danh sách Model từ cao xuống thấp bằng chính cái Key này
#                     for model_name in MODELS:
#                         try:
#                             print(f"[AnalyzeTab] Đang thử phân tích bằng model: {model_name}...")
#                             response = client.models.generate_content(
#                                 model=model_name,
#                                 contents=prompt
#                             )
                            
#                             if response.text:
#                                 ai_analysis = response.text.strip()
#                                 break  # ✨ ĐÃ THÀNH CÔNG: Thoát ngay khỏi vòng lặp model!
                                
#                         except APIError as e:
#                             # Nếu dính 429 (Hết lượt) hoặc 503 (Nghẽn mạng), tiếp tục thử model thấp hơn của Key này
#                             if e.code in [429, 503]:
#                                 print(f"⚠️ Model {model_name} lỗi ({e.code}) khi phân tích. Đang thử model tiếp theo...")
#                                 continue 
#                             else:
#                                 print(f"❌ Lỗi API khác tại {model_name}: {e}")
#                                 continue
                                
#                         except Exception as e:
#                             print(f"❌ Lỗi xử lý tại {model_name}: {e}")
#                             continue

#                     # Nếu vòng lặp trong đã tìm được model chạy thành công, thoát luôn vòng lặp Key
#                     if ai_analysis:
#                         break

#                     # Nếu đã vét cạn sạch danh sách model của Key này mà vẫn thất bại, tiến hành đổi Key tiếp theo
#                     print("[AnalyzeTab] Key hiện tại dính lỗi trên mọi model. Đang đảo sang API Key tiếp theo...")
#                     if not GeminiClientManager.rotate_key():
#                         break  # Không còn key dự phòng nào thì dừng hẳn
                        
#                 except Exception as e:
#                     print(f"❌ Lỗi hệ thống quản lý Key: {e}")
#                     break

#             # Nếu quét sạch sành sanh cả kho Key lẫn kho Model mà không ông nào chạy được
#             if not ai_analysis:
#                 return (
#                     f"❌ Tất cả các model AI và API Key hiện tại đều hết lượt dùng (429) hoặc lỗi hệ thống.\n\n"
#                     f"📄 Không thể phân tích tự động, bạn có thể xem tạm 300 ký tự thô cào được:\n{web_text_content[:300]}..."
#                 )

#             # Đóng khung kết quả đẹp đẽ để Telegram hiển thị chi tiết
#             output_message = (
#                 f"🧠 *PHÂN TÍCH NỘI DUNG TAB CHROME*\n"
#                 f"📌 *Tab:* {tab_title}\n"
#                 f"🔗 *Nguồn:* {tab_url if tab_url else 'Cào trực tiếp từ màn hình OS'}\n"
#                 f"----------------------------------------\n\n"
#                 f"{ai_analysis}"
#             )
#             return output_message

#         except Exception as e:
#             return f"❌ Gặp lỗi khi gửi dữ liệu cho Gemini AI xử lý: {str(e)}\n\n📄 Bạn có thể xem tạm 300 ký tự đầu cào được:\n{web_text_content[:300]}..."
from activities.BaseActivity import BaseActivity
from config import MODELS, GEMINI_API_KEYS
from service.GeminiClientManager import GeminiClientManager
from service.ChromeManager import ChromeManager
from google.genai.errors import APIError


class AnalyzeChromeTabActivity(BaseActivity):

    NAME = "AnalyzeChromeTabActivity"
    DESCRIPTION = """
    Trích xuất toàn bộ nội dung chữ của một tab Chrome (theo index hoặc từ khóa)
    và sử dụng Gemini AI để phân tích, tóm tắt lại nội dung chính.
    """

    PARAMETERS = {
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab cần phân tích (1, 2, 3...).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa trong tiêu đề để tìm tab cần phân tích.",
            "required": False,
            "default": None
        },
        "remote_port": {
            "type": "integer",
            "description": "Cổng Debug của Chrome",
            "required": False,
            "default": 9222
        }
    }

    EXAMPLES = [
        "Phân tích tab số 3",
        "Tóm tắt nội dung tab google docs",
        "Đọc nội dung tab index=5",
        "Xem tab số 2 viết về cái gì"
    ]

    @staticmethod
    def execute(context=None, index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")
        
        # Khởi tạo ChromeManager gánh vác logic nền tảng
        manager = ChromeManager(context=context, remote_port=remote_port, user_id=user_id)
        
        # 1. Tìm tab mục tiêu (Logic đã đẩy vào Manager)
        target_tab, error_msg = manager.find_tab_by_target(index=index, keyword=keyword)
        if error_msg:
            return error_msg

        # 2. Trích xuất text nội dung (Logic đã đẩy vào Manager)
        web_text_content = manager.extract_tab_text(target_tab)

        # Kiểm tra độ dài văn bản thu được
        if not web_text_content or len(web_text_content.strip()) < 10:
            return f"❌ Không thể trích xuất nội dung văn bản từ tab:\n📌 *{target_tab.title}*\n(Có thể trang web trống hoặc chưa tải xong)."

        # Giới hạn token đầu vào cho AI
        web_text_content = web_text_content[:8000]

        # 3. Chuẩn bị Prompt gửi AI
        prompt = f"""
        Bạn là một trợ lý AI phân tích nội dung trang web chuyên nghiệp.
        Hãy đọc và phân tích nội dung văn bản thô được trích xuất từ trang web dưới đây.
        
        Thông tin trang web:
        - Tiêu đề: {target_tab.title}
        - Đường dẫn: {target_tab.url}
        
        Nội dung văn bản thô:
        \"\"\"
        {web_text_content}
        \"\"\"
        
        Yêu cầu phản hồi:
        1. Tóm tắt ngắn gọn trang web này nói về cái gì (2-3 câu).
        2. Liệt kê từ 3 đến 5 ý chính quan trọng nhất dưới dạng gạch đầu dòng.
        3. Đưa ra đánh giá nhanh hoặc phân loại thể loại của trang web này (Ví dụ: Tin tức, Công việc, Tài liệu kỹ thuật, Giải trí...).
        
        Viết câu trả lời bằng tiếng Việt, rõ ràng, gãy gọn, không sử dụng các ký tự markdown nguy hiểm bọc ngoài tiêu đề.
        """

        ai_analysis = None

        # 4. Giữ nguyên 100% logic vòng lặp kép thông minh: Quét xoay tua API Key & hạ cấp Model khi dính 429
        for _ in range(len(GEMINI_API_KEYS)):
            try:
                client = GeminiClientManager.get_client()
                
                for model_name in MODELS:
                    try:
                        print(f"[AnalyzeTab] Đang thử phân tích bằng model: {model_name}...")
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        
                        if response.text:
                            ai_analysis = response.text.strip()
                            break # Thành công model -> Thoát vòng lặp model
                            
                    except APIError as e:
                        if e.code in [429, 503]:
                            print(f"⚠️ Model {model_name} lỗi ({e.code}). Đang hạ cấp thử model tiếp theo...")
                            continue 
                        else:
                            print(f"❌ Lỗi API khác tại {model_name}: {e}")
                            continue
                    except Exception as e:
                        print(f"❌ Lỗi xử lý tại {model_name}: {e}")
                        continue

                if ai_analysis:
                    break # Thành công có dữ liệu -> Thoát vòng lặp xoay tua Key

                print("[AnalyzeTab] Đang đảo sang tài khoản API Key tiếp theo...")
                if not GeminiClientManager.rotate_key():
                    break
                    
            except Exception as e:
                print(f"❌ Lỗi hệ thống quản lý Key: {e}")
                break

        # Nếu vét cạn tài nguyên mà vẫn lỗi
        if not ai_analysis:
            return (
                f"❌ Tất cả các model AI và API Key hiện tại đều hết lượt dùng (429) hoặc lỗi hệ thống.\n\n"
                f"📄 Không thể phân tích tự động, bạn có thể xem tạm 300 ký tự thô cào được:\n{web_text_content[:300]}..."
            )

        # Trả kết quả đóng gói đẹp đẽ về cho Telegram nhận diện hiển thị
        return (
            f"🧠 *PHÂN TÍCH NỘI DUNG TAB CHROME*\n"
            f"📌 *Tab:* {target_tab.title}\n"
            f"🔗 *Nguồn:* {target_tab.url if target_tab.url else 'Cào trực tiếp từ màn hình OS'}\n"
            f"----------------------------------------\n\n"
            f"{ai_analysis}"
        )