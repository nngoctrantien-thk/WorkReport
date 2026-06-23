# import http.client
# import json
# import re
# import win32gui
# import win32process
# import psutil
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from activities.BaseActivity import BaseActivity

# try:
#     from pywinauto import Desktop
# except ImportError:
#     Desktop = None


# def sanitize_telegram_text(text):
#     """
#     Làm sạch text, xóa bỏ Null byte và ký tự lạ gây vỡ tin nhắn Telegram
#     """
#     if not text:
#         return ""
#     text = str(text)
#     text = text.replace('\x00', '')
#     text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
#     clean_text = re.sub(r'[*_`\[\]()~>#+\-=|{}.!<>&]', '', text)
#     return clean_text.replace('\n', ' ').replace('\r', ' ').strip()


# class CheckChromeTabsActivity(BaseActivity):

#     NAME = "CheckChromeTabsActivity"
#     DESCRIPTION = "Quét CHÍNH XÁC tab của Google Chrome, loại bỏ VS Code và Chatwork."
#     PARAMETERS = {
#         "remote_port": {"type": "integer", "description": "Cổng Debug", "required": False, "default": 9222}
#     }

#     @staticmethod
#     def execute(context=None, remote_port=9222, **kwargs):
#         tabs_data = []      
#         telegram_views = []  

#         # =================================================================
#         # TẦNG 1: QUÉT QUA DEBUG PORT (Ưu tiên số 1 vì có đầy đủ URL)
#         # =================================================================
#         try:
#             conn = http.client.HTTPConnection("127.0.0.1", remote_port, timeout=1)
#             conn.request("GET", "/json/list")
#             res = conn.getresponse()
            
#             if res.status == 200:
#                 chrome_all_targets = json.loads(res.read().decode('utf-8'))
#                 for target in chrome_all_targets:
#                     if target.get("type") == "page":
#                         raw_title = target.get("title", "Tab khong co tieu de")
#                         raw_url = target.get("url", "")
                        
#                         tabs_data.append({
#                             "handle": target.get("id", ""),
#                             "title": raw_title,
#                             "url": raw_url,
#                             "source": "chrome_api"
#                         })
                        
#                         clean_title = sanitize_telegram_text(raw_title)
#                         clean_url = sanitize_telegram_text(raw_url)
                        
#                         idx = len(telegram_views) + 1
#                         telegram_views.append(f"{idx}. 📌 Tiêu đề: {clean_title}\n🔗 Link: {clean_url}")
#         except Exception:
#             pass

#         # =================================================================
#         # TẦNG 2: CÀO GIAO DIỆN UI (CHỈ LẤY CHROME THẬT, BỎ ELECTRON APPS)
#         # =================================================================
#         if Desktop is not None:
#             try:
#                 # Lấy tất cả các cửa sổ có class lõi Chromium
#                 windows = Desktop(backend="uia").windows(class_name="Chrome_WidgetWin_1")
                
#                 for win in windows:
#                     try:
#                         # LẤY PID VÀ TÊN TIẾN TRÌNH CỦA CỬA SỔ NÀY
#                         _, pid = win32process.GetWindowThreadProcessId(win.handle)
#                         proc = psutil.Process(pid)
#                         process_name = proc.name().lower()
                        
#                         # CHỈ CHẤP NHẬN CHROME THẬT (Bỏ qua code.exe, chatwork.exe, discord.exe...)
#                         if process_name != "chrome.exe":
#                             continue
                            
#                     except (psutil.NoSuchProcess, psutil.AccessDenied):
#                         continue  # Nếu lỗi phân quyền hoặc tiến trình đã đóng thì bỏ qua

#                     # Nếu đúng là Google Chrome thì mới tiến hành bóc tách các Tab
#                     tab_items = win.descendants(control_type="TabItem")
#                     for tab in tab_items:
#                         raw_title = tab.window_text()
                        
#                         # Loại bỏ các tab hệ thống trống hoặc tab "New Tab" không cần thiết nếu muốn
#                         if raw_title and raw_title != "Lưu lượng truy cập mạng":
#                             tabs_data.append({
#                                 "handle": None,
#                                 "title": raw_title,
#                                 "url": "",
#                                 "source": "ui_automation"
#                             })
#                             clean_title = sanitize_telegram_text(raw_title)
                            
#                             idx = len(telegram_views) + 1
#                             telegram_views.append(f"{idx}. 📌 Tab: {clean_title}")
                            
#             except Exception as e:
#                 print(f"[CheckTabs] Loi UI: {str(e)}")

#         # =================================================================
#         # ĐẨY VÀO CONTEXT & TRẢ VỀ
#         # =================================================================
#         if not telegram_views:
#             return "❌ Không tìm thấy bất kỳ tab Google Chrome thực sự nào đang mở."

#         if context is not None:
#             context["chrome_tabs"] = tabs_data

#         user_id = kwargs.get("user_id", "global")
#         try:
#             with open(f"cache_tabs_{user_id}.json", "w", encoding="utf-8") as f:
#                 json.dump(tabs_data, f, ensure_ascii=False, indent=4)
#         except Exception:
#             pass

#         source_mode = tabs_data[0]["source"]
#         header = f"🤖 DANH SÁCH TAB CHROME ĐANG MỞ (Tổng cộng: {len(telegram_views)} tab):\n\n"
        
#         return header + "\n\n".join(telegram_views)

from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class CheckChromeTabsActivity(BaseActivity):

    NAME = "CheckChromeTabsActivity"
    DESCRIPTION = "Quét CHÍNH XÁC danh sách các tab đang mở của Google Chrome."
    
    PARAMETERS = {
        "remote_port": {
            "type": "integer", 
            "description": "Cổng Debug của Google Chrome", 
            "required": False, 
            "default": 9222
        }
    }

    EXAMPLES = [
        "Kiểm tra danh sách tab",
        "Xem đang mở những tab nào",
        "Quét các tab chrome"
    ]

    @staticmethod
    def execute(context=None, remote_port=9222, **kwargs):
        # Lấy thông tin user_id từ arguments đầu vào
        user_id = kwargs.get("user_id", "global")

        # Khởi tạo ChromeManager để tái sử dụng toàn bộ hệ thống lõi đã tối ưu
        manager = ChromeManager(
            context=context, 
            remote_port=remote_port, 
            user_id=user_id
        )

        # 1. Thực hiện quét 2 tầng (API + UI Automation), tự động lưu Context và Cache JSON
        tabs = manager.scan()

        # 2. Kiểm tra nếu không tìm thấy tab nào
        if not tabs:
            return "❌ Không tìm thấy bất kỳ tab Google Chrome thực sự nào đang mở."

        # 3. Định dạng danh sách kết quả an toàn bằng TextUtils để gửi lên Telegram
        return manager.format_telegram(tabs)
        