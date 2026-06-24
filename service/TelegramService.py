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
        file_path = None
        send_as_file = False
        
        try:
            # Chạy toàn bộ chuỗi workflow (Open Browser -> Summarize -> Screenshot hoặc Print ID)
            response = TelegramCommandModel.execute(text)

            # Nếu kết quả trả về là một dict (chuỗi các bước chạy thành công)
            if isinstance(response, dict):
                # Lấy các đường dẫn tài nguyên nếu có
                screenshot_path = response.get("screenshot_path")
                file_path = response.get("telegram_file_path")
                send_as_file = response.get("telegram_send_as_file", False)

            # Định dạng kết quả chữ (ví dụ: nội dung tóm tắt) để chuẩn bị gửi
            message = TelegramFormatter.format(response)

        except Exception as e:
            print(e)
            message = f"❌ Hệ thống gặp lỗi: {str(e)}"

        # =================================================================
        # 1. XỬ LÝ GỬI TIN NHẮN CHỮ HOẶC FILE VĂN BẢN (CHỐNG LỖI 413)
        # =================================================================
        
        # Trường hợp A: Có lệnh ép gửi bằng file từ Activity quét ID
        if send_as_file and file_path and os.path.exists(str(file_path)):
            try:
                with open(file_path, 'rb') as doc_file:
                    await update.message.reply_document(
                        document=doc_file,
                        filename=os.path.basename(file_path),
                        caption="🤖 Cấu trúc ID chi tiết của ứng dụng bạn yêu cầu đây nhé!"
                    )
                # Dọn dẹp file text tạm trên ổ cứng sau khi upload thành công
                os.remove(file_path)
                print(f"Đã gửi file cấu trúc và dọn dẹp: {file_path}")
            except Exception as file_err:
                print(f"Lỗi gửi file cấu trúc: {file_err}")
                await update.message.reply_text(f"⚠️ Gặp lỗi khi tải file ID lên Telegram: {str(file_err)}")
                
        else:
            # Trường hợp B: Tin nhắn văn bản bình thường nhưng độ dài vượt biên (> 4000 ký tự)
            if message and len(message) > 4000:
                try:
                    fallback_file_path = "long_response_output.txt"
                    with open(fallback_file_path, "w", encoding="utf-8") as f:
                        f.write(message)
                        
                    with open(fallback_file_path, "rb") as doc_file:
                        await update.message.reply_document(
                            document=doc_file,
                            filename="ket_qua_chi_tiet.txt",
                            caption="📝 Kết quả phản hồi quá dài, hệ thống tự động chuyển đổi thành file để bảo vệ luồng tin nhắn."
                        )
                    os.remove(fallback_file_path)
                except Exception as fallback_err:
                    print(f"Lỗi tầng bảo vệ text dài: {fallback_err}")
                    await update.message.reply_text(f"❌ Kết quả quá dài và lỗi phát sinh khi tạo file cứu hộ: {str(fallback_err)}")
            else:
                # Tin nhắn ngắn an toàn, gửi như bình thường
                await update.message.reply_text(message)

        # =================================================================
        # 2. GỬI ẢNH SCREENSHOT (Nếu có)
        # =================================================================
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