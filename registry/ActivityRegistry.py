import inspect
import importlib
import pkgutil
import json
import activities


class ActivityRegistry:

    def __init__(self):
        self.activities = {}
        self.load()

    def load(self):
        for _, module_name, _ in pkgutil.iter_modules(activities.__path__):
            module = importlib.import_module(f"activities.{module_name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if hasattr(cls, "execute") and cls.__module__.startswith("activities."):
                    self.activities[cls.__name__] = cls

    def get(self, name):
        return self.activities.get(name)

    def list(self):
        return self.activities

    def get_details_for_prompt(self):
        details = []
        for name, cls in self.activities.items():
            desc = getattr(cls, "DESCRIPTION", "Không có mô tả.").strip()
            params = getattr(cls, "PARAMETERS", {})
            examples = getattr(cls, "EXAMPLES", [])
            
            # Format cấu trúc rõ ràng cho AI đọc
            item = (
                f"TÊN ACTIVITY: {name}\n"
                f"MÔ TẢ: {desc}\n"
                f"CÁC THAM SỐ NHẬN VÀO:\n{json.dumps(params, ensure_ascii=False, indent=2)}\n"
                f"VÍ DỤ CÂU LỆNH: {', '.join(examples) if examples else 'Không có'}\n"
                f"---------------------------------------"
            )
            details.append(item)
        return "\n\n".join(details)