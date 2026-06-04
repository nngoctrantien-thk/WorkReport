class ForEachDataTableActivity:

    @staticmethod
    def execute(data):

        for index, row in enumerate(data):
            yield index, row