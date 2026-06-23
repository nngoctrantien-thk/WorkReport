import json
import os
from activities.BaseActivity import BaseActivity


class UpdateConfigModelsActivity(BaseActivity):

    NAME = "UpdateConfigModelsActivity"
    DESCRIPTION = """
    Cập nhật và thay đổi cấu hình Model AI (Gemini) được sử dụng trong hệ thống trực tiếp từ Telegram.
    Lưu cấu hình vào file để các lệnh sau tự động đọc theo.
    """

    PARAMETERS = {
        "model_name": {
            "type": "string",
            "description": "Tên dòng model muốn đổi sang (Ví dụ: gemini-2.0-flash, gemini-2.0-flash-lite).",
            "required": True
        }
    }

    EXAMPLES = [
        "Đổi model sang gemini-2.0-flash",
        "Cập nhật cấu hình model gemini-2.0-flash-lite",
        "Set model gemini-1.5-flash",
        "Thay đổi AI sang dòng lite"
    ]

    # Danh sách các model Gemini chính thức được hệ thống hỗ trợ (Chống gõ nhầm gây lỗi 404)
    VALID_MODELS = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
    ]

    @staticmethod
    def execute(context=None, model_name=None, **kwargs):
        if not model_name:
            return "❌ Vui lòng cung cấp tham số 'model_name' (Ví dụ: gemini-2.0-flash)."

        # Chuẩn hóa chuỗi nhập vào của user
        clean_model_name = str(model_name).lower().strip()

        # =================================================================
        # BƯỚC 1: KIỂM TRA TÊN MODEL XEM CÓ HỢP LỆ KHÔNG
        # =================================================================
        if clean_model_name not in UpdateConfigModelsActivity.VALID_MODELS:
            valid_list_str = "\n".join([f"• {m}" for m in UpdateConfigModelsActivity.VALID_MODELS])
            return (
                f"❌ Model '{model_name}' không được hỗ trợ hoặc không tồn tại!\n\n"
                f"🤖 Vui lòng chọn một trong các model chuẩn sau:\n{valid_list_str}"
            )

        # =================================================================
        # BƯỚC 2: GHI ĐÈ CẤU HÌNH MỚI VÀO FILE PERSISTENCE (JSON)
        # =================================================================
        config_file = "bot_config.json"
        config_data = {}

        # Đọc cấu hình cũ lên trước nếu có để tránh làm mất các cài đặt khác
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}

        # Cập nhật model mới vào cấu hình
        config_data["active_model"] = clean_model_name

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            print(f"[UpdateConfig] Đã cập nhật active_model thành: {clean_model_name}")
        except Exception as e:
            return f"❌ Lỗi hệ thống khi ghi file cấu hình: {str(e)}"

        # Đồng thời cập nhật vào context hiện tại nếu phiên làm việc đang sống
        if context is not None:
            context["active_model"] = clean_model_name

        # =================================================================
        # BƯỚC 3: TRẢ VỀ KẾT QUẢ (Có dấu \\n để bypass bộ lọc _short của bạn)
        # =================================================================
        output_message = (
            f"⚙️ CẬP NHẬT CẤU HÌNH THÀNH CÔNG\n"
            f"🤖 Model hiện tại: {clean_model_name}\n"
            f"----------------------------------------\n"
            f"✨ Kể từ lệnh sau, các hoạt động phân tích dữ liệu và tóm tắt tab sẽ tự động áp dụng dòng AI mới này."
        )
        return output_message