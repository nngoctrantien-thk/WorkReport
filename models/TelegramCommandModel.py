from models.GeminiModel import GeminiModel
from dispatcher.ActivityDispatcher import ActivityDispatcher


class TelegramCommandModel:

    dispatcher = ActivityDispatcher()
    
    # =================================================================
    # BỘ NHỚ LƯU TRỮ: Lưu vết lịch sử chat theo từng User ID riêng biệt
    # Cấu trúc: { "user_123": [ {"role": "user", "text": "..."}, {"role": "model", "text": "..."} ] }
    # =================================================================
    USER_HISTORIES = {}

    @staticmethod
    def execute(text, **kwargs):
        if not text:
            return "Dạ, em chưa nhận được nội dung tin nhắn từ anh/chị ạ."

        # Lấy thông tin ID người dùng để phân tách bộ nhớ, mặc định là "global" nếu chạy test
        user_id = str(kwargs.get("user_id", "global"))

        # Khởi tạo bộ nhớ cho người dùng mới nếu chưa từng chat
        if user_id not in TelegramCommandModel.USER_HISTORIES:
            TelegramCommandModel.USER_HISTORIES[user_id] = []

        text_str = str(text).strip()

        # Định hình khuôn mẫu tính cách bắt buộc xưng "em" và dẫn chứng xác thực
        persona_instruction = (
            "Bạn là một trợ lý AI tuyệt vời, cực kỳ ngoan ngoãn, lễ phép, chu đáo và thông minh. "
            "Nhiệm vụ của bạn là trả lời tất cả các yêu cầu thông tin có thể tìm kiếm và bắt buộc phải "
            "đưa ra dẫn chứng xác thực, chính xác, có nguồn tin cậy rõ ràng chứ TUYỆT ĐỐI KHÔNG ĐƯỢC BỊA ĐẶT thông tin. "
            "Nếu thông tin không chắc chắn hoặc không thể tìm kiếm, hãy thành thật báo lại với người dùng. "
            "QUY TẮC BẮT BUỘC: Khi trả lời hoặc trò chuyện với người dùng, bạn CHỈ ĐƯỢC PHÉP xưng là 'em' "
            "(tuyệt đối không xưng là 'tôi', 'mình', 'AI' hoặc bất kỳ từ nào khác). "
            "Luôn giữ thái độ lịch sự, dạ vâng ngọt ngào và sẵn sàng hỗ trợ hết mình."
        )

        # Lấy ra danh sách 5 câu hội thoại gần nhất của User này từ bộ nhớ
        current_history = TelegramCommandModel.USER_HISTORIES[user_id][-5:]

        # --- LUỒNG 1: ÉP BUỘC CHAT TỰ DO KHI GÕ DẤU "/" ĐẦU TIÊN ---
        if text_str.startswith("/"):
            clean_prompt = text_str[1:].strip()
            if not clean_prompt:
                return "Dạ em nghe đây ạ! Em thấy anh/chị gõ dấu `/` nhưng chưa nhập nội dung cần tra cứu. Anh/chị cần em tìm kiếm thông tin gì thế ạ?"
            
            ai_reply = GeminiModel.generate_text_free(
                prompt=clean_prompt, 
                system_instruction=persona_instruction,
                history=current_history # Đẩy lịch sử vào
            )
            
            # LƯU VẾT VÀO BỘ NHỚ: Cập nhật lượt chat mới vào kho
            TelegramCommandModel.USER_HISTORIES[user_id].append({"role": "user", "text": clean_prompt})
            TelegramCommandModel.USER_HISTORIES[user_id].append({"role": "model", "text": ai_reply})
            return ai_reply

        # --- LUỒNG 2: KIỂM TRA ĐỊNH TUYẾN TỰ ĐỘNG HÓA WORKFLOW ---
        action = GeminiModel.detect_activity(text_str)
        workflow = action.get("workflow", [])
        is_none_activity = workflow and workflow[0].get("activity") == "NONE"

        # Nếu không tìm thấy công cụ, tự động biến hình thành Trợ lý chat thường có nhớ bối cảnh
        if not workflow or is_none_activity:
            ai_reply = GeminiModel.generate_text_free(
                prompt=text_str, 
                system_instruction=persona_instruction,
                history=current_history # Đẩy lịch sử vào
            )
            
            # LƯU VẾT VÀO BỘ NHỚ
            TelegramCommandModel.USER_HISTORIES[user_id].append({"role": "user", "text": text_str})
            TelegramCommandModel.USER_HISTORIES[user_id].append({"role": "model", "text": ai_reply})
            return ai_reply

        # Nếu là lệnh điều khiển máy tính (Activity), chạy robot và không cần nạp vào lịch sử chat thường
        return TelegramCommandModel.dispatcher.dispatch(workflow)