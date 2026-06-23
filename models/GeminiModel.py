import json
from google.genai.errors import APIError
from registry.ActivityRegistry import ActivityRegistry
from config import MODELS, GEMINI_API_KEYS 
from service.GeminiClientManager import GeminiClientManager 


class GeminiModel:

    @staticmethod
    def detect_activity(text):
        registry = ActivityRegistry()
        
        # ✨ THAY ĐỔI QUAN TRỌNG: Lấy full tài liệu hướng dẫn của từng Activity ném vào prompt
        activities_documentation = registry.get_details_for_prompt()

        prompt = f"""
Bạn là AI Workflow Router chuyên nghiệp. Nhiệm vụ của bạn là phân tích yêu cầu của người dùng và chuyển đổi nó thành một chuỗi các bước thực hiện (workflow) chứa các Activity phù hợp theo đúng thứ tự logic.

Dưới đây là danh sách TÀI LIỆU HƯỚNG DẪN các Activity hiện có trong hệ thống (Hãy đọc kỹ Mô tả và Tham số để chọn cho đúng):
---------------------------------------
{activities_documentation}

Yêu cầu định dạng đầu ra bắt buộc phải là một JSON object có cấu trúc như sau:
{{
    "workflow": [
        {{
            "activity": "Tên_Activity_1",
            "params": {{ "tham_so_1": "gia_tri" }}
        }}
    ]
}}

⚠️ LƯU Ý QUAN TRỌNG VỀ THAM SỐ (PARAMS):
- Chỉ được phép sử dụng các tham số đã được định nghĩa trong mục "CÁC THAM SỐ NHẬN VÀO" của Activity đó. Tuyệt đối không tự bịa ra tham số mới (Ví dụ: không tự ý bịa ra tham số 'target' nếu trong tài liệu không có).
- Nếu người dùng không cung cấp thông tin cho tham số, hãy bỏ qua hoặc để mặc định.
- Nếu hoàn toàn không có Activity nào phù hợp, trả về:
{{
    "workflow": [
        {{
            "activity": "NONE",
            "params": {{}}
        }}
    ]
}}

Chỉ trả về JSON hợp lệ. Không bọc trong ```json. Không giải thích gì thêm.

Người dùng yêu cầu:
{text}
"""

        models_to_try = MODELS

        for _ in range(len(GEMINI_API_KEYS)):
            try:
                client = GeminiClientManager.get_client()
                
                for model_name in models_to_try:
                    try:
                        print(f"[Router] Đang thử model: {model_name} bằng Key hiện tại...")
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        
                        result = (response.text or "").strip()
                        if not result:
                            continue  

                        if result.startswith("```"):
                            lines = result.splitlines()
                            lines = [l for l in lines if not l.startswith("```")]
                            result = "\n".join(lines).strip()

                        data = json.loads(result)
                        if isinstance(data, dict) and "workflow" in data:
                            return data
                        if isinstance(data, list):
                            return {"workflow": data}
                        return {"workflow": [data]}

                    except APIError as e:
                        if e.code == 429 or e.code == 503:
                            print(f"⚠️ Model {model_name} lỗi ({e.code}). Thử model dự phòng...")
                            continue 
                        else:
                            print(f"❌ Lỗi API khác tại {model_name}: {e}")
                            continue
                            
                    except Exception as e:
                        print(f"❌ Lỗi xử lý tại {model_name}: {e}")
                        continue

                print("[Router] Key hiện tại không chạy được model nào. Đang đảo sang tài khoản API Key tiếp theo...")
                if not GeminiClientManager.rotate_key():
                    break  
                        
            except Exception as e:
                print(f"❌ Lỗi hệ thống quản lý Key: {e}")
                break

        return GeminiModel._none()

    @staticmethod
    def _none():
        return {"workflow": [{"activity": "NONE", "params": {}}]}