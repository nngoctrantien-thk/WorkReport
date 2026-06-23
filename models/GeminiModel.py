import json
from google.genai.errors import APIError
from google.genai import types # Dùng để cấu hình System Instruction và Lịch sử hội thoại
from registry.ActivityRegistry import ActivityRegistry
from config import MODELS, GEMINI_API_KEYS 
from service.GeminiClientManager import GeminiClientManager 


class GeminiModel:

    @staticmethod
    def detect_activity(text):
        registry = ActivityRegistry()
        
        # Lấy full tài liệu hướng dẫn của từng Activity ném vào prompt
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

    # =================================================================
    # ✨ NÂNG CẤP HOÀN CHỈNH: CHAT TỰ DO CÓ KHẢ NĂNG NHỚ LỊCH SỬ HỘI THOẠI
    # =================================================================
    @staticmethod
    def generate_text_free(prompt, system_instruction=None, history=None):
        """
        Sinh văn bản tự do (Chat tự do) có khả năng ghi nhớ ngữ cảnh cũ từ mảng history.
        Tự động đóng gói cấu trúc types.Content để tương thích tuyệt đối với bộ SDK mới.
        """
        models_to_try = MODELS
        
        # Đóng gói cấu hình chỉ thị tính cách trợ lý theo chuẩn SDK mới
        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        ) if system_instruction else None

        # Khởi tạo mảng payload chứa toàn bộ dữ liệu hội thoại (Lịch sử + Câu hỏi mới)
        contents_payload = []
        
        # 1. Nạp các câu hội thoại cũ (nếu có) từ bộ lưu trữ của TelegramCommandModel chuyển xuống
        if history and isinstance(history, list):
            for turn in history:
                contents_payload.append(
                    types.Content(
                        role=turn.get("role", "user"), # "user" hoặc "model"
                        parts=[types.Part(text=turn.get("text", ""))]
                    )
                )
        
        # 2. Đính kèm câu hỏi hiện tại của người dùng vào cuối danh sách payload
        contents_payload.append(
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        )

        # Tiến hành gọi API vòng lặp kết hợp quản lý Key Rotation chống nghẽn
        for _ in range(len(GEMINI_API_KEYS)):
            try:
                client = GeminiClientManager.get_client()
                
                for model_name in models_to_try:
                    try:
                        print(f"[Chat] Đang gọi phản hồi kèm bộ nhớ ngữ cảnh bằng model: {model_name}...")
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents_payload, # Truyền cấu trúc mảng đa tầng chứa lịch sử
                            config=config
                        )
                        
                        result = (response.text or "").strip()
                        if result:
                            return result
                            
                    except APIError as e:
                        if e.code in [429, 503]:
                            print(f"⚠️ Model {model_name} bận ({e.code}) trong luồng Chat. Thử model khác...")
                            continue
                        else:
                            print(f"❌ Lỗi API Chat tại {model_name}: {e}")
                            continue
                    except Exception as e:
                        print(f"❌ Lỗi xử lý sinh văn bản tại {model_name}: {e}")
                        continue
                
                print("[Chat] Key hiện tại lỗi hạn mức. Đang chuyển sang API Key tiếp theo...")
                if not GeminiClientManager.rotate_key():
                    break
                    
            except Exception as e:
                print(f"❌ Lỗi hệ thống quản lý Key trong luồng Chat: {e}")
                break

        return "Dạ vâng ạ, hệ thống kết nối của em đang gặp một chút xíu trục trặc nhỏ. Anh/chị đợi em một lát rồi ra lệnh lại cho em nhé! ❤️"

    @staticmethod
    def _none():
        return {"workflow": [{"activity": "NONE", "params": {}}]}