from registry.ActivityRegistry import ActivityRegistry


class ActivityDispatcher:

    def __init__(self):
        self.registry = ActivityRegistry()

    def dispatch(self, workflow):

        context = {}

        for step in workflow:

            activity_name = step.get("activity")
            params = step.get("params", {})

            activity_class = self.registry.get(activity_name)

            if not activity_class:
                raise Exception(f"Activity not found: {activity_name}")

            result = activity.execute(context=context, **params)

            context[activity_name] = result

        return context