from utils.FileUtils import FileUtils
from service.CacheManager import CacheManager


class ConfigManager:

    @classmethod
    def load(cls):

        return CacheManager.load(

            FileUtils.config(),

            {}
        )

    @classmethod
    def save(cls, config):

        CacheManager.save(

            FileUtils.config(),

            config
        )

    @classmethod
    def get(cls, key, default=None):

        cfg = cls.load()

        return cfg.get(key, default)

    @classmethod
    def set(cls, key, value):

        cfg = cls.load()

        cfg[key] = value

        cls.save(cfg)

    @classmethod
    def active_model(cls):

        return cls.get("active_model")

    @classmethod
    def set_active_model(cls, model):

        cls.set("active_model", model)