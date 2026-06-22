import json

from google import genai
from registry.ActivityRegistry import ActivityRegistry
from config import GEMINI_API_KEY


class GeminiModel:

    client = genai.Client(api_key=GEMINI_API_KEY)

    @staticmethod
    def detect_activity(text):

        registry = ActivityRegistry()

        activities = "\n".join(
            f"- {name}" for name in registry.list().keys()
        )

        prompt = f"""
Bạn là AI Router.

Các Activity hiện có:

{activities}

Nhiệm vụ:

- Chỉ chọn đúng Activity có trong danh sách.
- Nếu không có Activity phù hợp thì trả về:

{{
    "activity": "NONE",
    "params": {{}}
}}

Chỉ trả về JSON hợp lệ.
Không sử dụng ```json hoặc ``` để bao quanh.
Không giải thích.

Ví dụ:

Người dùng:
mở google

Trả về:

{{
    "activity": "OpenBrowserActivity",
    "params": {{
        "url": "https://google.com"
    }}
}}

Người dùng:
{text}
"""

        try:
            response = GeminiModel.client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            result = (response.text or "").strip()

            if not result:
                raise ValueError("Gemini trả về nội dung rỗng.")

            # Loại bỏ markdown nếu có
            if result.startswith("```"):
                lines = result.splitlines()

                if lines and lines[0].startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]

                result = "\n".join(lines).strip()

            return json.loads(result)

        except json.JSONDecodeError:
            print("Không parse được JSON từ Gemini:")
            print(result)

        except Exception as e:
            print(f"Lỗi khi gọi Gemini: {e}")

        return {
            "activity": "NONE",
            "params": {}
        }