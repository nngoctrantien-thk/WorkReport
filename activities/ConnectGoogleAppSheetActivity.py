from config import GOOGLE_APPLICATION_ACCESS_KEY, GOOGLE_APP_ID


class ConnectGoogleAppSheetActivity:

    @staticmethod
    def execute(api):
        api.authenticate(
            GOOGLE_APPLICATION_ACCESS_KEY,
            GOOGLE_APP_ID
        )

        return api