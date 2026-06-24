import os
import json
import time
import re
from activities.BaseActivity import BaseActivity
from config import MODELS, GEMINI_API_KEYS
from service.GeminiClientManager import GeminiClientManager
from service.ChromeManager import ChromeManager
from google.genai.errors import APIError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class AnalyzeChromeTabActivity(BaseActivity):

    NAME = "AnalyzeChromeTabActivity"
    DESCRIPTION = """
    Trích xuất cấu trúc cây thư mục DOM Tree (Dạng Toàn bộ trang hoặc Dạng Rút gọn) của một tab Chrome,
    lưu trữ vào file JSON cache local. Nếu có tham số query sẽ tìm XPath, nếu không sẽ tóm tắt cấu trúc trang.
    """

    PARAMETERS = {
        "query": {
            "type": "string",
            "description": "Mô tả phần tử hoặc nút cần tìm kiếm XPath (ví dụ: 'nút Đăng nhập'). Nếu muốn quét lưu cache tổng quan thì không cần truyền.",
            "required": False,
            "default": None
        },
        "mode": {
            "type": "string",
            "description": "Chế độ phân tích cấu trúc: 'compact' (chỉ lấy thẻ tương tác) hoặc 'full' (lấy toàn bộ cấu trúc tất cả các thẻ).",
            "required": False,
            "default": "compact"
        },
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab cần phân tích (1, 2, 3...).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa trong tiêu đề hoặc URL để tìm tab cần phân tích.",
            "required": False,
            "default": None
        },
        "remote_port": {
            "type": "integer",
            "description": "Cổng Debug điều khiển từ xa của Chrome",
            "required": False,
            "default": 9222
        }
    }

    EXAMPLES = [
        "Phân tích toàn bộ tab số 12",
        "Quét lưu cache tab số 3",
        "Tìm xpath của nút đăng nhập ở tab số 1"
    ]

    @staticmethod
    def execute(context=None, query=None, mode="compact", index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")
        
        # Chuẩn hóa chế độ quét
        analysis_mode = str(mode).lower().strip()
        if analysis_mode not in ["compact", "full"]:
            analysis_mode = "compact"
        
        # Khởi tạo ChromeManager đảm nhiệm việc quét và tương tác tab
        manager = ChromeManager(context=context, remote_port=remote_port, user_id=user_id)
        
        # 1. Định vị tab mục tiêu
        target_tab, error_msg = manager.find_tab_by_target(index=index, keyword=keyword)
        if error_msg:
            return error_msg

        dom_tree_content = ""
        is_fallback_text = False

        # Định nghĩa sẵn các kịch bản Javascript bóc tách cấu trúc
        if analysis_mode == "full":
            js_extract_dom = """
            const elements = document.querySelectorAll('*');
            const fullTree = [];
            elements.forEach((el) => {
                const tag = el.tagName.toLowerCase();
                if (['script', 'style', 'meta', 'link', 'noscript', 'head'].includes(tag)) return;
                
                const importantAttrs = ['id', 'class', 'name', 'type', 'placeholder', 'value', 'aria-label', 'role', 'href'];
                const attrs = {};
                importantAttrs.forEach(attr => {
                    if (el.hasAttribute(attr)) {
                        attrs[attr] = el.getAttribute(attr);
                    }
                });
                
                let directText = "";
                if (el.childNodes.length > 0) {
                    for (let node of el.childNodes) {
                        if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
                            directText = node.nodeValue.trim().substring(0, 50);
                            break;
                        }
                    }
                }
                
                fullTree.push({
                    tag: tag,
                    text: directText || (el.innerText && el.innerText.length < 40 ? el.innerText.trim() : ''),
                    attrs: attrs
                });
            });
            return JSON.stringify(fullTree);
            """
        else:
            js_extract_dom = """
            const elements = document.querySelectorAll('input, button, a, select, textarea, [role="button"], form, [id], [onclick]');
            const compactTree = [];
            elements.forEach((el) => {
                const importantAttrs = ['id', 'class', 'name', 'type', 'placeholder', 'value', 'aria-label', 'role', 'href'];
                const attrs = {};
                importantAttrs.forEach(attr => {
                    if (el.hasAttribute(attr)) {
                        attrs[attr] = el.getAttribute(attr);
                    }
                });
                
                compactTree.push({
                    tag: el.tagName.toLowerCase(),
                    text: el.innerText ? el.innerText.trim().substring(0, 80) : '',
                    attrs: attrs
                });
            });
            return JSON.stringify(compactTree);
            """

        # =================================================================
        # ✨ SIÊU NÂNG CẤP: ƯU TIÊN SỐ 1 - TRÍCH XUẤT TRỰC TIẾP TỪ DRIVER LIVE TRONG RAM
        # Nếu bước trước vừa gọi OpenBrowserActivity, driver này đang giữ trang mới mở!
        # =================================================================
        driver = context.get("driver") if context else None
        if driver:
            try:
                print("[AnalyzeTab] Phát hiện Driver đang kích hoạt trong RAM Context. Cào DOM trực tiếp không cần cổng Debug...")
                dom_tree_content = driver.execute_script(js_extract_dom)
            except Exception as e:
                print(f"[AnalyzeTab] Trích xuất từ live driver không thành công, chuyển sang luồng dự phòng: {e}")

        # =================================================================
        # TẦNG 2: LUỒNG DỰ PHÒNG - KẾT NỐI QUA CỔNG DEBUG PORT THEO HANDLE CỦA TAB
        # =================================================================
        if not dom_tree_content:
            source_str = target_tab.source.value if hasattr(target_tab.source, 'value') else str(target_tab.source)
            if source_str in ["chrome_api", "selenium"] and target_tab.handle:
                is_temp_driver = False
                try:
                    if not driver:
                        options = Options()
                        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_port}")
                        driver = webdriver.Chrome(options=options)
                        is_temp_driver = True

                    driver.switch_to.window(target_tab.handle)
                    dom_tree_content = driver.execute_script(js_extract_dom)
                    
                    if is_temp_driver:
                        driver.quit()
                except Exception as e:
                    print(f"[AnalyzeTab] Lỗi bóc tách cấu trúc DOM qua cổng Debug Port: {str(e)}")

        # TẦNG 3: LUỒNG CUỐI CÙNG - CÀO TEXT THÔ QUA UI AUTOMATION
        if not dom_tree_content:
            dom_tree_content = manager.extract_tab_text(target_tab)
            is_fallback_text = True

        if not dom_tree_content or len(dom_tree_content.strip()) < 10:
            return f"❌ Không thể trích xuất dữ liệu cấu trúc hoặc văn bản từ tab:\n📌 *{target_tab.title}*"

        # 3. GHI VÀO FILE CACHE / JSON LOCAL ĐỂ CÁC BƯỚC KHÁC ĐỐI CHIẾU
        cache_dir = "cache_dom"
        os.makedirs(cache_dir, exist_ok=True)
        safe_title = "".join([c for c in target_tab.title if c.isalnum() or c in (' ', '_', '-')]).rstrip()
        cache_file_name = f"dom_{user_id}_{index or 'kw'}_{safe_title[:15]}.json"
        cache_file_path = os.path.join(cache_dir, cache_file_name)

        try:
            cache_payload = {
                "tab_title": target_tab.title,
                "tab_url": target_tab.url,
                "analysis_mode": analysis_mode,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_fallback_text": is_fallback_text,
                "dom_data": json.loads(dom_tree_content) if not is_fallback_text else dom_tree_content
            }
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(cache_payload, f, ensure_ascii=False, indent=4)
            print(f"[AnalyzeTab] Đã lưu DOM Tree vào cache JSON thành công: {cache_file_path}")
        except Exception as e:
            print(f"[AnalyzeTab] Lỗi ghi file cache JSON: {e}")

        # Tự động điều chỉnh giới hạn độ dài
        max_chars = 35000 if analysis_mode == "full" else 15000
        truncated_dom = dom_tree_content[:max_chars]

        # 4. Tạo Prompt động thích ứng theo việc có hay không có tham số query
        if query:
            task_instruction = f'YÊU CẦU ĐẶC ĐIỂM PHẦN TỬ CẦN TÌM XPATH: "{query}"'
            output_format = """
            Kết quả phản hồi bắt buộc tuân theo định dạng cấu trúc sau:
            - **Trạng thái**: [Tìm thấy / Không tìm thấy / Nghi ngờ trùng lặp]
            - **XPath đề xuất chính thức**: `đường_dẫn_xpath_chính`
            - **Các giải pháp XPath dự phòng**: 
              1. `xpath_dự_phòng_1`
              2. `xpath_dự_phòng_2`
            - **Thuộc tính cấu trúc nhận diện**: Tag, ID, Class hoặc Text của thẻ được lựa chọn.
            - **Hướng dẫn cho Bot**: Giải thích lý do lựa chọn và khuyến nghị hành động thích hợp (Click, Nhập text).
            """
        else:
            task_instruction = "YÊU CẦU: Phân tích tổng quan và lập bản đồ các thành phần tương tác chính trên trang web này để phục vụ cho các bước chạy Automation tiếp theo."
            output_format = """
            Kết quả phản hồi bắt buộc tuân theo định dạng cấu trúc sau:
            - **Trạng thái**: [Đã lưu Cache thành công]
            - **Tổng quan trang web**: Mô tả ngắn gọn trang này chứa giao diện gì (2-3 câu).
            - **Các thành phần tương tác cốt lõi phát hiện được**: Liệt kê danh sách các Form nhập liệu, Ô Input quan trọng, hoặc Nút bấm nổi bật (kèm ID/Name/Text của chúng nếu có) dưới dạng gạch đầu dòng để bot có thể tra cứu và tương tác sau này.
            """

        prompt = f"""
        Bạn là một chuyên gia kỹ sư Automation chuyên sâu về Selenium và Playwright Automation.
        Hãy phân tích dữ liệu cấu trúc bề mặt trang web được cung cấp dưới đây.
        
        Thông tin trang web:
        - Tiêu đề: {target_tab.title}
        - Đường dẫn: {target_tab.url}
        - Chế độ quét dữ liệu: {analysis_mode.upper()} MODE
        - Dạng dữ liệu đầu vào: {"Văn bản thô (Mất cấu trúc HTML)" if is_fallback_text else "JSON DOM Tree"}
        
        {task_instruction}
        
        Cấu trúc dữ liệu trang web:
        \"\"\"
        {truncated_dom}
        \"\"\"
        
        {output_format}

        Viết câu trả lời bằng tiếng Việt rõ ràng, ngắn gọn, gãy gọn, không dùng các ký tự bọc ngoài tiêu đề gây lỗi hiển thị.
        """

        ai_analysis = None

        # 5. GIỮ NGUYÊN 100% LOGIC VÒNG LẶP KÉP QUẢN LÝ KEY & MODEL
        for _ in range(len(GEMINI_API_KEYS)):
            try:
                client = GeminiClientManager.get_client()
                
                for model_name in MODELS:
                    try:
                        print(f"[AnalyzeTab] Đang phân tích dữ liệu bằng model: {model_name}...")
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        
                        if response.text:
                            ai_analysis = response.text.strip()
                            break
                            
                    except APIError as e:
                        if e.code in [429, 503]:
                            print(f"⚠️ Model {model_name} lỗi nghẽn ({e.code}). Đang thử model tiếp theo...")
                            continue 
                        else:
                            print(f"❌ Lỗi API khác tại {model_name}: {e}")
                            continue
                    except Exception as e:
                        print(f"❌ Lỗi hệ thống xử lý tại {model_name}: {e}")
                        continue

                if ai_analysis:
                    break

                print("[AnalyzeTab] Đang đảo sang API Key tài khoản tiếp theo...")
                if not GeminiClientManager.rotate_key():
                    break
                    
            except Exception as e:
                print(f"❌ Lỗi nghiêm trọng tại hệ thống quản lý Key: {e}")
                break

        if not ai_analysis:
            return (
                f"❌ Tất cả các model AI và API Key hệ thống hiện tại đều hết lượt dùng (429) hoặc gặp sự cố mạng.\n\n"
                f"📂 Dẫu vậy, tệp tin DOM Tree ({analysis_mode}) đã kết xuất lưu trữ thành công tại cache local:\n`{cache_file_path}`"
            )

        # =================================================================
        # 🔗 VÙNG BẮC CẦU: GOM SẠCH TẤT CẢ XPATH TRONG DẤU ` CỦA GEMINI VÀO RAM
        # =================================================================
        if context is not None and query:
            all_codes = re.findall(r"`([^`]+)`", ai_analysis)
            candidates = []
            for code in all_codes:
                code_clean = code.strip()
                if code_clean.startswith("/") or code_clean.startswith("./") or code_clean.startswith("("):
                    if code_clean not in candidates:
                        candidates.append(code_clean)
            
            if candidates:
                context["last_resolved_xpath_candidates"] = candidates
                context["last_resolved_xpath"] = candidates[0]
                print(f"🔗 [AnalyzeTab] Đã đồng bộ {len(candidates)} ứng viên XPath vào RAM Context.")

        # Trả thông tin đóng gói về cho Telegram điều phối
        header_title = f"PHÂN TÍCH XPATH ({analysis_mode.upper()} MODE)" if query else f"LẬP BẢN ĐỒ CACHE DOM ({analysis_mode.upper()} MODE)"
        return (
            f"🤖 *HỆ THỐNG {header_title}*\n"
            f"📌 *Tab:* {target_tab.title}\n"
            f"📂 *File Cache:* `{cache_file_path}`\n"
            f"----------------------------------------\n\n"
            f"{ai_analysis}"
        )