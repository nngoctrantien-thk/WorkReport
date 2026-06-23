import re


class TextUtils:

    CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f-\x9f]')
    MARKDOWN = re.compile(r'[*_`\[\]()~>#+\-=|{}.!<>&]')

    @staticmethod
    def sanitize(text):

        if text is None:
            return ""

        text = str(text)

        text = text.replace("\x00", "")

        text = TextUtils.CONTROL_CHARS.sub("", text)

        text = TextUtils.MARKDOWN.sub("", text)

        return (
            text
            .replace("\n", " ")
            .replace("\r", " ")
            .strip()
        )