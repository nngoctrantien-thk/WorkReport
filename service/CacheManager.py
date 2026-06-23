import json
from pathlib import Path

from service.Logger import get_logger

logger = get_logger(__name__)


class CacheManager:

    @staticmethod
    def load(path, default=None):

        path = Path(path)

        if default is None:
            default = {}

        if not path.exists():
            return default

        try:

            with open(path, encoding="utf8") as f:
                return json.load(f)

        except Exception as e:

            logger.exception(e)

            return default

    @staticmethod
    def save(path, data):

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(

            path,

            "w",

            encoding="utf8"

        ) as f:

            json.dump(

                data,

                f,

                ensure_ascii=False,

                indent=4
            )

    @staticmethod
    def clear_json(path):

        CacheManager.save(path, [])

    @staticmethod
    def clear_text(path):

        path = Path(path)

        with open(

            path,

            "w",

            encoding="utf8"

        ) as f:

            f.write("")