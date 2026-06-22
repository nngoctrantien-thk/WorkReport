import json


class TelegramFormatter:

    @staticmethod
    def format(response):

        if response is None:
            return "Done."

        if isinstance(response, str):
            return response

        if isinstance(response, (int, float)):
            return str(response)

        if isinstance(response, dict):
            return json.dumps(response, ensure_ascii=False, indent=2)

        if isinstance(response, list):
            return json.dumps(response, ensure_ascii=False, indent=2)

        # Selenium / object / class instance
        return f"[{response.__class__.__name__}] completed."