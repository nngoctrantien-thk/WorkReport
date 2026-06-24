import os
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class ClickOnBrowserActivity(BaseActivity):

    NAME = "ClickOnBrowserActivity"
    DESCRIPTION = """
    Click (nhấp chuột) vào một phần tử cụ thể trên trang web.
    Hệ thống tích hợp chiến lược thử sai cuốn chiếu kết hợp bộ dò JS Smart-Hunter 
    để triệt tiêu hoàn toàn lỗi tương tác trên các nền tảng phức tạp.
    """

    PARAMETERS = {
        "selector": {
            "type": "string",
            "description": "Selector dạng CSS, đường dẫn XPath hoặc tên/chuỗi chữ hiển thị của phần tử cần click.",
            "required": True
        },
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab cần thao tác click (1, 2, 3...).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa tiêu đề hoặc URL để nhận diện tab cần thao tác click.",
            "required": False,
            "default": None
        },
        "remote_port": {
            "type": "integer",
            "description": "Cổng Debug của Chrome đang chạy",
            "required": False,
            "default": 9222
        }
    }

    @staticmethod
    def execute(context=None, selector=None, index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")

        if not selector:
            return "❌ Thất bại: Thiếu tham số 'selector' để xác định phần tử cần click."

        manager = ChromeManager(context=context, remote_port=remote_port, user_id=user_id)
        target_tab, _ = manager.find_tab_by_target(index=index, keyword=keyword)

        candidates = []
        is_plain_text = False
        if not (selector.startswith("/") or selector.startswith("./") or selector.startswith("(")):
            if not any(c in selector for c in ['#', '.', '[', ']', '>', ':', '=']):
                is_plain_text = True

        # =================================================================
        # 🧪 THU THẬP NGUỒN 1: TOÀN BỘ DANH SÁCH CÁC XPATH TỪ RAM CONTEXT
        # =================================================================
        if context and context.get("last_resolved_xpath_candidates"):
            for cand in context["last_resolved_xpath_candidates"]:
                if ('XPATH', cand) not in candidates: candidates.append(('XPATH', cand))
        elif context and context.get("last_resolved_xpath"):
            candidates.append(('XPATH', context["last_resolved_xpath"]))

        # =================================================================
        # 🧪 THU THẬP NGUỒN 2: TRA CỨU FILE CACHE JSON LOCAL
        # =================================================================
        if target_tab and is_plain_text:
            cache_dir = "cache_dom"
            if os.path.exists(cache_dir):
                for f in os.listdir(cache_dir):
                    if f.endswith(".json"):
                        try:
                            cache_file_path = os.path.join(cache_dir, f)
                            with open(cache_file_path, "r", encoding="utf-8") as file:
                                cache_payload = json.load(file)
                            
                            if cache_payload.get("tab_url") == target_tab.url or target_tab.title in cache_payload.get("tab_title", ""):
                                dom_elements = cache_payload.get("dom_data", [])
                                sel_lower = selector.lower().strip()
                                
                                for el in dom_elements:
                                    tag = el.get("tag", "*")
                                    text = el.get("text", "")
                                    attrs = el.get("attrs", {})
                                    
                                    if (attrs.get("id") and attrs.get("id").lower() == sel_lower) or (attrs.get("name") and attrs.get("name").lower() == sel_lower):
                                        cx = f"//*[@id='{attrs.get('id')}']" if attrs.get("id") else f"//{tag}[@name='{attrs.get('name')}']"
                                        if ('XPATH', cx) not in candidates: candidates.append(('XPATH', cx))
                                    elif text and sel_lower in text.lower():
                                        cx = f"//{tag}[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_lower}')]"
                                        if ('XPATH', cx) not in candidates: candidates.append(('XPATH', cx))
                        except Exception:
                            continue

        # =================================================================
        # 🧪 THU THẬP NGUỒN 3: BỘ QUÉT LIVE SCAN TRƯỜNG PHÁI TỰ CHỮA LÀNH ĐỘNG
        # =================================================================
        if is_plain_text:
            sel_clean = selector.strip().lower()
            sel_clean_text = re.sub(r'[\(\)]', '', sel_clean).strip()
            live_xpaths = [
                f"//*[@id='{sel_clean}']",
                f"//*[@name='{sel_clean}']",
                f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_clean_text}')]",
                f"//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_clean_text}')]",
                f"//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_clean_text}')]"
            ]
            for lx in live_xpaths:
                if ('XPATH', lx) not in candidates: candidates.append(('XPATH', lx))

        orig_type = 'XPATH' if (selector.startswith("/") or selector.startswith("./") or selector.startswith("(")) else 'CSS'
        if (orig_type, selector) not in candidates: candidates.append((orig_type, selector))

        # =================================================================
        # 🚀 THỰC THI KIỂM THỬ TRÊN BROWSER LIVE
        # =================================================================
        driver = context.get("driver") if context else None
        if not driver:
            try:
                options = Options()
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
                driver = webdriver.Chrome(options=options)
                if context is not None: context["driver"] = driver
            except Exception as e:
                return f"❌ Không thể kết nối với trình duyệt Chrome. Lỗi: {str(e)}"

        if target_tab and target_tab.handle:
            try: driver.switch_to.window(target_tab.handle)
            except Exception: pass

        success = False
        final_used_selector = ""
        error_logs = []

        # --- VÒNG LẶP SƠ CỦA CUỐN CHIẾU (TRIAL LOOP) ---
        for idx, (by_str, sel_str) in enumerate(candidates):
            by_type = By.XPATH if by_str == 'XPATH' else By.CSS_SELECTOR
            try:
                element = driver.find_element(by_type, sel_str)
                if element and element.is_displayed():
                    print(f"sử dụng selector là : {sel_str} ")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.2)
                    try: element.click()
                    except Exception: driver.execute_script("arguments[0].click();", element)
                    success = True
                    final_used_selector = sel_str
                    break
            except Exception as ex:
                error_logs.append(f"Ứng viên #{idx+1} (`{sel_str}`) trượt: {str(ex).splitlines()[0]}")
                continue

        if success:
            return f"🎯 Đã tìm thấy và click thành công dựa trên cấu trúc chuẩn hóa: '{final_used_selector}'."
        else:
            return f"❌ Thất bại hoàn toàn sau khi duyệt thử toàn bộ {len(candidates)} giải pháp Selector.\n\n📄 Lịch sử lỗi:\n" + "\n".join(error_logs[:5])