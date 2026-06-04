class ReadGoogleAppSheetDataActivity:

    @staticmethod
    def execute(api, table_name):
        return api.read_range(table_name)