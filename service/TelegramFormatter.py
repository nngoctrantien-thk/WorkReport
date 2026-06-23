import json


class TelegramFormatter:

    @staticmethod
    def format(response):
        if response is None:
            return "Done."

        if isinstance(response, str):
            return response

        if isinstance(response, bool):
            return "True" if response else "False"

        if isinstance(response, (int, float)):
            return str(response)

        if isinstance(response, dict):
            return TelegramFormatter._format_dict(response)

        if isinstance(response, list):
            return TelegramFormatter._format_list(response)

        return f"[{response.__class__.__name__}] completed."

    @staticmethod
    def _format_dict(data):
        lines = []
        for k, v in data.items():
            if isinstance(v, str) and "\n" in v:
                lines.append(f"====== {k} ======\n{TelegramFormatter._short(v)}")
            else:
                lines.append(f"{k}: {TelegramFormatter._short(v)}")
        return "\n".join(lines)

    @staticmethod
    def _format_list(data):
        return f"List[{len(data)} items]\n" + "\n".join(
            f"- {TelegramFormatter._short(x)}" for x in data[:5]
        )

    @staticmethod
    def _short(value):
        if isinstance(value, dict):
            return f"dict({len(value)})"

        if isinstance(value, list):
            return f"list({len(value)})"

        if isinstance(value, str):
            if "\n" in value:
                return value
            
            return value[:200]

        return str(value)