from models.GeminiModel import GeminiModel
from dispatcher.ActivityDispatcher import ActivityDispatcher


class TelegramCommandModel:

    dispatcher = ActivityDispatcher()

    @staticmethod
    def execute(text):

        action = GeminiModel.detect_activity(text)
        workflow = action.get("workflow", [])

        if not workflow:
            return "Không tìm thấy workflow."
        # check NONE phải lấy phần tử đầu tiên
        first_step = workflow[0]
        
        # if first_step.get("activity") == "NONE":
        #     return "Xin lỗi, tôi chưa có Activity phù hợp."

        return TelegramCommandModel.dispatcher.dispatch(workflow)