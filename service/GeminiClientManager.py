# service/GeminiClientManager.py
from google import genai
from config import GEMINI_API_KEYS

class GeminiClientManager:
    _current_key_index = 0
    _client = None

    @classmethod
    def get_client(cls):
        """Lấy client hiện tại, nếu chưa có thì khởi tạo"""
        if cls._client is None:
            if not GEMINI_API_KEYS:
                raise Exception("Không tìm thấy GEMINI_API_KEYS trong file config.py")
            current_key = GEMINI_API_KEYS[cls._current_key_index]
            cls._client = genai.Client(api_key=current_key)
        return cls._client

    @classmethod
    def rotate_key(cls):
        """Chuyển sang API Key tiếp theo trong danh sách"""
        if len(GEMINI_API_KEYS) <= 1:
            print("⚠️ Chỉ có 1 API Key, không thể đảo Key!")
            return False
            
        cls._current_key_index = (cls._current_key_index + 1) % len(GEMINI_API_KEYS)
        next_key = GEMINI_API_KEYS[cls._current_key_index]
        
        print(f"🔄 Đang tự động đổi sang API Key vị trí số: {cls._current_key_index}")
        # Khởi tạo lại client với key mới
        cls._client = genai.Client(api_key=next_key)
        return True