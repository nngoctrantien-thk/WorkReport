import os
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class TypeOnBrowserActivity(BaseActivity):

    NAME = "TypeOnBrowserActivity"
    DESCRIPTION = """
    Nhập dữ liệu văn bản vào một ô nhập liệu (Input, Textarea, ContentEditable) trên trang web.
    Hệ thống tích hợp bộ lọc cuốn chiếu thử sai liên tục kết hợp JS Smart-Hunter để xử lý các ô chat AI.
    """

    PARAMETERS = {
        "selector": {
            "type": "string",
            "description": "Selector dạng CSS, đường dẫn XPath hoặc tên/nhãn chữ mô tả của ô nhập liệu.",
            "required": True
        },
        "text": {
            "type": "string",
            "description": "Nội dung văn bản cần điền vào.",
            "required": True
        },
        "clear_before": {
            "type": "boolean",
            "description": "Xóa sạch chữ đang có sẵn trong ô nhập liệu trước khi gõ chữ mới hay không.",
            "required": False,
            "default": True
        },
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab chứa phần tử nhập liệu (1, 2, 3...).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa tiêu đề hoặc URL nhằm xác minh đúng tab cần điền text.",
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
    def execute(context=None, selector=None, text="", clear_before=True, index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")

        if not selector:
            return "❌ Thất bại: Thiếu tham số 'selector' để xác định ô nhập liệu."

        manager = ChromeManager(context=context, remote_port=remote_port, user_id=user_id)
        target_tab, _ = manager.find_tab_by_target(index=index, keyword=keyword)

        candidates = []
        is_plain_text = False
        if not (selector.startswith("/") or selector.startswith("./") or selector.startswith("(")):
            if not any(c in selector for c in ['#', '.', '[', ']', '>', ':', '=']):
                is_plain_text = True

        # =================================================================
        # 🧪 NGUỒN 1: DANH SÁCH ỨNG VIÊN TỪ RAM CONTEXT
        # =================================================================
        if context and context.get("last_resolved_xpath_candidates"):
            for cand in context["last_resolved_xpath_candidates"]:
                if ('XPATH', cand) not in candidates: candidates.append(('XPATH', cand))
        elif context and context.get("last_resolved_xpath"):
            candidates.append(('XPATH', context["last_resolved_xpath"]))

        # =================================================================
        # 🧪 NGUỒN 2: TRA CỨU FILE CACHE JSON LOCAL
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
                                    tag = el.get("tag", "input")
                                    text_val = el.get("text", "")
                                    attrs = el.get("attrs", {})
                                    
                                    if (attrs.get("id") and attrs.get("id").lower() == sel_lower) or (attrs.get("name") and attrs.get("name").lower() == sel_lower):
                                        cx = f"//*[@id='{attrs.get('id')}']" if attrs.get("id") else f"//{tag}[@name='{attrs.get('name')}']"
                                        if ('XPATH', cx) not in candidates: candidates.append(('XPATH', cx))
                                    elif attrs.get("placeholder") and sel_lower in attrs.get("placeholder").lower():
                                        cx = f"//{tag}[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_lower}')]"
                                        if ('XPATH', cx) not in candidates: candidates.append(('XPATH', cx))
                        except Exception:
                            continue

        # =================================================================
        # 🧪 NGUỒN 3: BỘ QUÉT LIVE SCAN TRƯỜNG PHÁI CASE-INSENSITIVE & AI INPUT
        # =================================================================
        if is_plain_text:
            sel_clean = selector.strip().lower()
            live_xpaths = [
                f"//*[@id='{sel_clean}']",
                f"//*[@name='{sel_clean}']",
                f"//*[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_clean}')]",
                f"//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sel_clean}')]",
                f"//div[@contenteditable='true']",  # Thẻ chí mạng ăn thẳng vào ô chat Gemini/ChatGPT
                f"//*[contains(@class, 'ql-editor')]",  # Class đặc trưng của Quill Editor trên Gemini
                f"//*[@role='textarea' or @role='textbox']"
            ]
            for lx in live_xpaths:
                if ('XPATH', lx) not in candidates: candidates.append(('XPATH', lx))

        # NGUỒN 4: THÊM CHÍNH NÓ LÀM PHƯƠNG ÁN CUỐI CÙNG
        orig_type = 'XPATH' if (selector.startswith("/") or selector.startswith("./") or selector.startswith("(")) else 'CSS'
        if (orig_type, selector) not in candidates: candidates.append((orig_type, selector))

        # =================================================================
        # 🚀 THỰC THI VÒNG LẶP THỬ SAI KẾT HỢP JS SMART-HUNTER
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

        # --- VŨ KHÍ TỐI THƯỢNG: CHẠY JS SMART-HUNTER TRƯỚC KHI QUÉT XPATH CỨNG ---
        if is_plain_text:
            try:
                print(f"🎯 [TypeActivity] Đang kích hoạt JS Smart-Hunter cho chuỗi: '{selector}'")
                js_hunter_script = """
                const query = arguments[0].toLowerCase();
                // Ưu tiên tìm các vùng chat đặc thù trước
                if (query.includes('gemini') || query.includes('tin nhắn') || query.includes('câu lệnh') || query.includes('ask')) {
                    const aiInput = document.querySelector('div[contenteditable="true"], .ql-editor, [role="textbox"]');
                    if (aiInput) return aiInput;
                }
                const elements = document.querySelectorAll('input, textarea, div[contenteditable="true"], [role="textbox"]');
                for (let el of elements) {
                    if (!el.getBoundingClientRect().width || !el.getBoundingClientRect().height) continue; // Bỏ qua phần tử ẩn
                    
                    if ((el.id || '').toLowerCase() === query || 
                        (el.getAttribute('name') || '').toLowerCase() === query ||
                        (el.getAttribute('placeholder') || '').toLowerCase().includes(query) ||
                        (el.getAttribute('aria-label') || '').toLowerCase().includes(query)) {
                        return el;
                    }
                }
                return null;
                """
                js_element = driver.execute_script(js_hunter_script, selector)
                if js_element:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", js_element)
                    time.sleep(0.2)
                    if clear_before:
                        try: js_element.clear()
                        except Exception: driver.execute_script("arguments[0].innerText = '';", js_element)
                    
                    # Thực hiện nhập văn bản (Hỗ trợ cả send_keys và JS fallback điền text)
                    try:
                        js_element.send_keys(str(text))
                    except Exception:
                        driver.execute_script("arguments[0].innerText = arguments[1];", js_element, str(text))
                    
                    print("⚡ [TypeActivity] JS Smart-Hunter đã xử lý ô nhập liệu thành công!")
                    return f"⌨️ Đã điền văn bản thành công vào ô nhập liệu bằng bộ dò tìm JS thông minh."
            except Exception as jse:
                print(f"⚠️ [TypeActivity] JS Smart-Hunter tạm thời bỏ qua do lỗi: {jse}")

        # --- VÒNG LẶP SƠ CUA: NẾU JS HUNTER TRƯỢT -> CHẠY TIẾP LUỒNG CUỐN CHIẾU CŨ ---
        for idx, (by_str, sel_str) in enumerate(candidates):
            by_type = By.XPATH if by_str == 'XPATH' else By.CSS_SELECTOR
            try:
                element = driver.find_element(by_type, sel_str)
                if element and element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.2)
                    if clear_before:
                        try: element.clear()
                        except Exception: pass
                    element.send_keys(str(text))
                    success = True
                    final_used_selector = sel_str
                    break
            except Exception as ex:
                error_logs.append(f"Ứng viên #{idx+1} (`{sel_str}`) trượt: {str(ex).splitlines()[0]}")
                continue

        if success:
            return f"⌨️ Đã điền thành công nội dung văn bản vào phần tử định vị: '{final_used_selector}'."
        else:
            return f"❌ Thất bại hoàn toàn sau khi duyệt thử tất cả {len(candidates)} giải pháp ô nhập liệu.\n\n📄 Lịch sử lỗi:\n" + "\n".join(error_logs[:5])