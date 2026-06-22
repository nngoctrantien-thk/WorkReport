from registry.ActivityRegistry import ActivityRegistry


class ActivityDispatcher:

    def __init__(self):
        self.registry = ActivityRegistry()

    def dispatch(self, data):

        activity_name = data.get("activity")

        params = data.get("params", {})

        activity = self.registry.get(activity_name)

        if activity is None:
            raise Exception(
                f"Activity '{activity_name}' not found."
            )

        return activity.execute(**params)