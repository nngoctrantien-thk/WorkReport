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
- Nếu không có Activity phù hợp thì trả:

{{
    "activity": "NONE",
    "params": {{}}
}}

Chỉ trả về JSON hợp lệ.
Không markdown.
Không giải thích.

Người dùng:
{text}
"""

        try:
            response = GeminiModel.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            result = (response.text or "").strip()

            if not result:
                return GeminiModel._none()

            # remove markdown
            if result.startswith("```"):
                lines = result.splitlines()
                lines = [l for l in lines if not l.startswith("```")]
                result = "\n".join(lines).strip()

            data = json.loads(result)

            # luôn normalize thành workflow
            return {
                "workflow": [data]
            }

        except Exception as e:
            print(f"Gemini error: {e}")
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