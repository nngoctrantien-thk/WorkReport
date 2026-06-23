import json
from google.genai.errors import APIError
from registry.ActivityRegistry import ActivityRegistry
from config import MODELS, GEMINI_API_KEYS # Import danh sách các Keys
from service.GeminiClientManager import GeminiClientManager # Import bộ quản lý Key


class GeminiModel:

    # BỎ dòng khai báo client cố định ở đây!

    @staticmethod
    def detect_activity(text):

        registry = ActivityRegistry()
        activities = "\n".join(
            f"- {name}" for name in registry.list().keys()
        )

        prompt = f"""
Bạn là AI Workflow Router. Nhiệm vụ của bạn là phân tích yêu cầu của người dùng và chuyển đổi nó thành một chuỗi các bước thực hiện (workflow) chứa các Activity phù hợp theo đúng thứ tự logic.

Các Activity hiện có trong hệ thống:
{activities}

Yêu cầu định dạng đầu ra bắt buộc phải là một JSON object có cấu trúc như sau:
{{
    "workflow": [
        {{
            "activity": "Tên_Activity_1",
            "params": {{ "tham_so_1": "gia_tri" }}
        }},
        {{
            "activity": "Tên_Activity_2",
            "params": {{}}
        }}
    ]
}}

Lưu ý quan trọng:
- Phân tích kỹ yêu cầu của người dùng để chia nhỏ thành các Activity tương ứng nếu họ yêu cầu làm nhiều việc cùng lúc.
- Chỉ chọn đúng các Activity có tên trong danh sách phía trên.
- Nếu hoàn toàn không có Activity nào phù hợp, trả về:
{{
    "workflow": [
        {{
            "activity": "NONE",
            "params": {{}}
        }}
    ]
}}

Chỉ trả về JSON hợp lệ.
Không bọc trong ký tự markdown (không dùng ```json).
Không giải thích gì thêm.

Người dùng:
{text}
"""

        models_to_try = MODELS

        # Duyệt qua từng đời Model (Ưu tiên chạy model tốt nhất trước)
        for model_name in models_to_try:
            
            # Vòng lặp con: Thử tối đa bằng số lượng API Key bạn đang cấu hình
            for _ in range(len(GEMINI_API_KEYS)):
                try:
                    # Lấy client động theo Key đang kích hoạt hiện tại
                    client = GeminiClientManager.get_client()
                    
                    print(f"[Router] Đang thử gọi model: {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    
                    result = (response.text or "").strip()
                    if not result:
                        break  # Nếu lỗi trả về rỗng, chuyển sang model tiếp theo

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
                    # NẾU DÍNH LỖI HẾT LƯỢT (429)
                    if e.code == 429:
                        print(f"⚠️ Key hiện tại đã HẾT QUOTA (429) khi gọi {model_name}!")
                        
                        # Gọi hàm đảo sang Key tiếp theo trong file GeminiClientManager
                        if GeminiClientManager.rotate_key():
                            print("🔄 Đã đổi sang Key mới thành công. Đang chạy lại...")
                            continue  # Lệnh này sẽ ép vòng lặp con chạy lại chính model này với Key mới!
                        else:
                            break  # Nếu không đổi được key, bẻ gãy vòng lặp
                            
                    elif e.code == 503:
                        print(f"⚠️ Model {model_name} bận (503). Chuyển sang model dự phòng...")
                        break  # Thoát vòng lặp con để nhảy sang model tiếp theo ở vòng lặp lớn
                    else:
                        print(f"❌ Lỗi API khác tại {model_name}: {e}")
                        break
                        
                except Exception as e:
                    print(f"❌ Lỗi hệ thống: {e}")
                    break

        return GeminiModel._none()

    @staticmethod
    def _none():
        return {
            "workflow": [
                {
                    "activity": "NONE",
                    "params": {}
                }
            ]
        }