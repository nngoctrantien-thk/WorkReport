# # import http.client
# # import json
# # import os
# # import re
# # import win32gui
# # import win32process
# # import psutil
# # from selenium import webdriver
# # from activities.BaseActivity import BaseActivity

# # try:
# #     from pywinauto import Desktop
# # except ImportError:
# #     Desktop = None


# # class CloseChromeTabActivity(BaseActivity):

# #     NAME = "CloseChromeTabActivity"
# #     DESCRIPTION = """
# #     Đóng một hoặc nhiều tab Chrome đang mở dựa vào danh sách đã lưu trước đó.
# #     Hỗ trợ đóng theo Số thứ tự (index) hoặc Từ khóa trong tiêu đề (keyword).
# #     """

# #     PARAMETERS = {
# #         "index": {
# #             "type": "integer",
# #             "description": "Số thứ tự của tab cần đóng (Ví dụ: 1, 2, 3... từ lệnh check tab trước).",
# #             "required": False,
# #             "default": None
# #         },
# #         "keyword": {
# #             "type": "string",
# #             "description": "Từ khóa nằm trong tiêu đề hoặc URL của tab muốn đóng (Ví dụ: 'facebook', 'sheets').",
# #             "required": False,
# #             "default": None
# #         },
# #         "remote_port": {
# #             "type": "integer",
# #             "description": "Cổng Debug của Chrome",
# #             "required": False,
# #             "default": 9222
# #         }
# #     }

# #     EXAMPLES = [
# #         "Đóng tab số 5",
# #         "Tắt tab facebook",
# #         "Close tab index=1",
# #         "Đóng tab chứa chữ google docs"
# #     ]

# #     @staticmethod
# #     def execute(context=None, index=None, keyword=None, remote_port=9222, **kwargs):
# #         user_id = kwargs.get("user_id", "global")
# #         file_cache_name = f"cache_tabs_{user_id}.json"
# #         saved_tabs = []

# #         # =================================================================
# #         # BƯỚC 1: LẤY LẠI DANH SÁCH TAB TỪ LỆNH TRƯỚC
# #         # =================================================================
# #         if context and context.get("chrome_tabs"):
# #             saved_tabs = context["chrome_tabs"]
# #             print("[CloseTab] Lấy danh sách tab thành công từ context.")
# #         elif os.path.exists(file_cache_name):
# #             try:
# #                 with open(file_cache_name, "r", encoding="utf-8") as f:
# #                     saved_tabs = json.load(f)
# #                 print("[CloseTab] Lấy danh sách tab thành công từ file JSON cache.")
# #             except Exception as e:
# #                 return f"❌ Lỗi khi đọc bộ nhớ tab cũ: {str(e)}"

# #         if not saved_tabs:
# #             return "❌ Không tìm thấy lịch sử tab nào trước đó. Vui lòng chạy lệnh 'Kiểm tra các tab đang mở' trước."

# #         # =================================================================
# #         # BƯỚC 2: XÁC ĐỊNH TAB CẦN ĐÓNG
# #         # =================================================================
# #         target_tab = None
# #         target_index = None

# #         # Trường hợp A: Tìm theo Số thứ tự (Index)
# #         if index is not None:
# #             target_index = int(index) - 1  # Chuyển từ 1-based (user xem) sang 0-based (lập trình)
# #             if 0 <= target_index < len(saved_tabs):
# #                 target_tab = saved_tabs[target_index]
# #             else:
# #                 return f"❌ Số thứ tự {index} không hợp lệ. Danh sách chỉ có từ 1 đến {len(saved_tabs)}."

# #         # Trường hợp B: Tìm theo Từ khóa (Keyword)
# #         elif keyword:
# #             keyword_clean = str(keyword).lower().strip()
# #             for i, tab in enumerate(saved_tabs):
# #                 title = str(tab.get("title", "")).lower()
# #                 url = str(tab.get("url", "")).lower()
# #                 if keyword_clean in title or keyword_clean in url:
# #                     target_tab = tab
# #                     target_index = i
# #                     break
# #             if not target_tab:
# #                 return f"❌ Không tìm thấy tab nào chứa từ khóa: '{keyword}'"
# #         else:
# #             return "❌ Vui lòng cung cấp số thứ tự tab (index) hoặc từ khóa (keyword) để đóng."

# #         # =================================================================
# #         # BƯỚC 3: TIẾN HÀNH ĐÓNG TAB THEO SOURCE
# #         # =================================================================
# #         tab_title = target_tab.get("title", "Không rõ tiêu đề")
# #         source = target_tab.get("source", "")
# #         handle = target_tab.get("handle")

# #         # --- CÁCH 1: Đóng qua Chrome Debug API (Rất sạch, đóng ngầm) ---
# #         if source == "chrome_api" and handle:
# #             try:
# #                 conn = http.client.HTTPConnection("127.0.0.1", remote_port, timeout=2)
# #                 # Chrome hỗ trợ gọi HTTP GET vào endpoint /json/close/{id} để đóng tab
# #                 conn.request("GET", f"/json/close/{handle}")
# #                 res = conn.getresponse()
# #                 if res.status == 200:
# #                     # Xóa tab đó khỏi danh sách lưu trữ hiện tại
# #                     saved_tabs.pop(target_index)
# #                     if context is not None:
# #                         context["chrome_tabs"] = saved_tabs
# #                     with open(file_cache_name, "w", encoding="utf-8") as f:
# #                         json.dump(saved_tabs, f, ensure_ascii=False, indent=4)
                        
# #                     return f"🗑️ Đã đóng thành công tab:\n📌 Tiêu đề: {tab_title}"
# #             except Exception as e:
# #                 print(f"[CloseTab] Lỗi đóng qua API: {str(e)}")

# #         # --- CÁCH 2: Đóng bằng Selenium Driver ---
# #         elif source == "selenium" and handle:
# #             try:
# #                 driver = context.get("driver") if context else None
# #                 if driver:
# #                     driver.switch_to.window(handle)
# #                     driver.close()
                    
# #                     saved_tabs.pop(target_index)
# #                     if context is not None:
# #                         context["chrome_tabs"] = saved_tabs
# #                     with open(file_cache_name, "w", encoding="utf-8") as f:
# #                         json.dump(saved_tabs, f, ensure_ascii=False, indent=4)
                        
# #                     # Trả driver về tab đầu tiên còn lại nếu có để tránh mất dấu
# #                     if driver.window_handles:
# #                         driver.switch_to.window(driver.window_handles[0])
                        
# #                     return f"🗑️ Đã đóng thành công tab qua Selenium:\n📌 Tiêu đề: {tab_title}"
# #             except Exception as e:
# #                 print(f"[CloseTab] Lỗi đóng qua Selenium: {str(e)}")

# #         # --- CÁCH 3: Đóng bằng UI Automation (Dự phòng cho việc Không Debug) ---
# #         elif Desktop is not None:
# #             try:
# #                 windows = Desktop(backend="uia").windows(class_name="Chrome_WidgetWin_1")
# #                 for win in windows:
# #                     # Kiểm tra xem cửa sổ có thuộc chrome.exe thật không
# #                     try:
# #                         import win32process, psutil
# #                         _, pid = win32process.GetWindowThreadProcessId(win.handle)
# #                         if psutil.Process(pid).name().lower() != "chrome.exe":
# #                             continue
# #                     except:
# #                         continue

# #                     # Tìm tab có tiêu đề trùng khớp để kích hoạt và gửi lệnh đóng
# #                     tab_items = win.descendants(control_type="TabItem")
# #                     for tab in tab_items:
# #                         if tab.window_text() == tab_title:
# #                             tab.click_input()      # Click chọn tab đó
# #                             win.type_keys('^w')    # Gửi tổ hợp phím Ctrl + W để đóng tab
                            
# #                             # Cập nhật lại bộ nhớ cache
# #                             saved_tabs.pop(target_index)
# #                             if context is not None:
# #                                 context["chrome_tabs"] = saved_tabs
# #                             with open(file_cache_name, "w", encoding="utf-8") as f:
# #                                 json.dump(saved_tabs, f, ensure_ascii=False, indent=4)
                                
# #                             return f"🗑️ Robot UI đã bấm đóng thành công tab:\n📌 Tiêu đề: {tab_title}"
# #             except Exception as e:
# #                 return f"❌ Lỗi khi cố gắng đóng giao diện UI: {str(e)}"

# #         return f"❌ Không thể đóng tab '{tab_title}' do mất kết nối tới trình duyệt."

# from activities.BaseActivity import BaseActivity
# from service.ChromeManager import ChromeManager


# class CloseChromeTabActivity(BaseActivity):

#     NAME = "CloseChromeTabActivity"
#     DESCRIPTION = """
#     Đóng một hoặc nhiều tab Chrome đang mở dựa vào danh sách đã lưu trước đó.
#     Hỗ trợ đóng theo Số thứ tự (index) hoặc Từ khóa trong tiêu đề (keyword).
#     """

#     PARAMETERS = {
#         "index": {
#             "type": "integer",
#             "description": "Số thứ tự của tab cần đóng (Ví dụ: 1, 2, 3... từ lệnh check tab trước).",
#             "required": False,
#             "default": None
#         },
#         "keyword": {
#             "type": "string",
#             "description": "Từ khóa nằm trong tiêu đề hoặc URL của tab muốn đóng (Ví dụ: 'facebook', 'sheets').",
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
#         "Đóng tab số 5",
#         "Tắt tab facebook",
#         "Close tab index=1",
#         "Đóng tab chứa chữ google docs"
#     ]

#     @staticmethod
#     def execute(
#         context=None,
#         index=None,
#         keyword=None,
#         remote_port=9222,
#         **kwargs
#     ):

#         manager = ChromeManager(
#             context=context,
#             remote_port=remote_port,
#             user_id=kwargs.get("user_id", "global")
#         )

#         manager.load_cache()

#         if index is not None:
#             tab = manager.find_by_index(index)

#         elif keyword:
#             tab = manager.find_by_keyword(keyword)

#         else:
#             return "❌ Vui lòng cung cấp index hoặc keyword."

#         if tab is None:
#             return "❌ Không tìm thấy tab."

#         return manager.close_tab(tab)
from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class CloseChromeTabActivity(BaseActivity):

    NAME = "CloseChromeTabActivity"
    DESCRIPTION = """
    Đóng một hoặc nhiều tab Chrome đang mở dựa vào danh sách đã lưu trước đó.
    Hỗ trợ đóng theo Số thứ tự (index) hoặc Từ khóa trong tiêu đề (keyword).
    """

    PARAMETERS = {
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab cần đóng (Ví dụ: 1, 2, 3... từ lệnh check tab trước).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa nằm trong tiêu đề hoặc URL của tab muốn đóng (Ví dụ: 'facebook', 'sheets').",
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
        "Đóng tab số 5",
        "Tắt tab facebook",
        "Close tab index=1",
        "Đóng tab chứa chữ google docs"
    ]

    @staticmethod
    def execute(context=None, index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")

        # Khởi tạo ChromeManager để gánh vác các logic nền tảng
        manager = ChromeManager(
            context=context,
            remote_port=remote_port,
            user_id=user_id
        )

        # =================================================================
        # BƯỚC 1: TÌM TAB MỤC TIÊU (Tự động đọc Context/Cache chuẩn từ Manager)
        # =================================================================
        target_tab, error_msg = manager.find_tab_by_target(index=index, keyword=keyword)
        if error_msg:
            return error_msg

        tab_title = target_tab.title

        # =================================================================
        # BƯỚC 2: TIẾN HÀNH ĐÓNG TAB (Tự động chạy chuỗi API -> Selenium -> UI)
        # =================================================================
        success = manager.close_tab(target_tab)

        if not success:
            return f"❌ Không thể đóng tab '{tab_title}' do mất kết nối tới trình duyệt hoặc bị hệ thống chặn."

        # =================================================================
        # BƯỚC 3: ĐỒNG BỘ HÓA CACHE & RAM (CONTEXT) SAU KHI ĐÓNG THÀNH CÔNG
        # =================================================================
        # 1. Loại bỏ tab đã đóng khỏi file JSON cache chuẩn (cache/tabs_global.json)
        new_tabs = manager.update_cache_after_close(user_id, target_tab)
        
        # 2. Đồng bộ cập nhật lại danh sách tab mới vào RAM (Context)
        ChromeManager.save_context(context, new_tabs)

        return f"🗑️ Đã đóng thành công tab:\n📌 Tiêu đề: {tab_title}"