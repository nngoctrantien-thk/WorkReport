from registry.ActivityRegistry import ActivityRegistry


class ActivityDispatcher:

    def __init__(self):
        self.registry = ActivityRegistry()

    def dispatch(self, workflow):

        context = {}

        for step in workflow:

            activity_name = step.get("activity")
            params = step.get("params", {})

            if activity_name == "NONE" or not activity_name:
                print("\n🤖 Bot thông báo: Tất cả các model AI hiện tại đều hết lượt dùng (429). Vui lòng thử lại sau vài phút!")
                return "Không thể thực hiện workflow do AI hết quota."

            # 2. Sau khi chắc chắn không phải "NONE" thì mới đi tìm class tương ứng
            activity_class = self.registry.get(activity_name)

            if activity_class is None:
                raise Exception(f"Activity not found: {activity_name}")

            # 3. Thực thi activity
            result = activity_class.execute(context=context, **params)
            context[activity_name] = result

        return context