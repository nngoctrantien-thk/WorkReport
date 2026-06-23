import os  # Thêm thư viện để kiểm tra file và xóa file ảnh tạm
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from service.TelegramFormatter import TelegramFormatter
from models.TelegramCommandModel import TelegramCommandModel


class TelegramService:

    def __init__(self, token):
        self.app = ApplicationBuilder().token(token).build()

        self.app.add_handler(
            MessageHandler(
                filters.TEXT,
                self.handler
            )
        )

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()

        print(f"User: {text}")

        screenshot_path = None
        try:
            # Chạy toàn bộ chuỗi workflow (Open Browser -> Summarize -> Screenshot)
            response = TelegramCommandModel.execute(text)

            # Nếu kết quả trả về là một dict (chuỗi các bước chạy thành công)
            if isinstance(response, dict):
                # Lấy đường dẫn ảnh được lưu từ ScreenshotActivity
                screenshot_path = response.get("screenshot_path")

            # Định dạng kết quả chữ (ví dụ: nội dung tóm tắt) để chuẩn bị gửi
            message = TelegramFormatter.format(response)

        except Exception as e:
            print(e)
            message = f"❌ Hệ thống gặp lỗi: {str(e)}"

        # 1. GỬI TIN NHẮN CHỮ TRƯỚC: Gửi kết quả tóm tắt hoặc thông báo lỗi cho User
        await update.message.reply_text(message)

        # 2. GỬI ẢNH SAU: Nếu tìm thấy đường dẫn ảnh và file đó thực sự tồn tại trên ổ cứng
        if screenshot_path and os.path.exists(str(screenshot_path)):
            try:
                # Mở file dưới dạng binary ('rb') và gửi qua reply_photo
                with open(screenshot_path, 'rb') as photo_file:
                    await update.message.reply_photo(
                        photo=photo_file,
                        caption="📸 Ảnh chụp màn hình trang web đi kèm."
                    )
                
                # Tùy chọn: Xóa file ảnh trên máy tính sau khi gửi xong để tránh làm đầy bộ nhớ
                os.remove(screenshot_path)
                print(f"Đã gửi ảnh thành công và dọn dẹp file: {screenshot_path}")

            except Exception as photo_err:
                print(f"Lỗi gửi ảnh: {photo_err}")
                await update.message.reply_text(f"⚠️ Không thể gửi kèm ảnh chụp màn hình: {str(photo_err)}")

    def run(self):
        self.app.run_polling()