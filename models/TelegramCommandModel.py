from models.GeminiModel import GeminiModel
from dispatcher.ActivityDispatcher import ActivityDispatcher


class TelegramCommandModel:

    dispatcher = ActivityDispatcher()

    @staticmethod
    def execute(text):

        action = GeminiModel.detect_activity(text)

        if action["activity"] == "NONE":
            return "Xin lỗi, tôi chưa có Activity phù hợp."

        return TelegramCommandModel.dispatcher.dispatch(action)