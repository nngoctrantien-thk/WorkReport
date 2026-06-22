import inspect
import importlib
import pkgutil

import activities


class ActivityRegistry:

    def __init__(self):
        self.activities = {}
        self.load()

    def load(self):

        for _, module_name, _ in pkgutil.iter_modules(activities.__path__):

            module = importlib.import_module(
                f"activities.{module_name}"
            )

            for _, cls in inspect.getmembers(
                module,
                inspect.isclass
            ):

                if hasattr(cls, "execute"):
                    self.activities[cls.__name__] = cls

    def get(self, name):
        return self.activities.get(name)

    def list(self):
        return self.activities