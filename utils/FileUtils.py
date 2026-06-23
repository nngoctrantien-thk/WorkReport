from pathlib import Path


class FileUtils:

    CACHE_FOLDER = Path("cache")

    @classmethod
    def ensure_cache_folder(cls):

        cls.CACHE_FOLDER.mkdir(
            parents=True,
            exist_ok=True
        )

    @classmethod
    def tab_cache(cls, user_id):

        cls.ensure_cache_folder()

        return cls.CACHE_FOLDER / f"tabs_{user_id}.json"

    @classmethod
    def config(cls):

        return Path("bot_config.json")