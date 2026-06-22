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

        try:
            response = TelegramCommandModel.execute(text)

            message = TelegramFormatter.format(response)

        except Exception as e:
            print(e)
            message = str(e)

        await update.message.reply_text(message)

    def run(self):
        self.app.run_polling()