from activities.BaseActivity import BaseActivity


class ForEachDataTableActivity(BaseActivity):

    NAME = "ForEachDataTableActivity"

    DESCRIPTION = """
    Lặp qua từng dòng của một bảng dữ liệu.
    Trả về danh sách gồm index và dữ liệu của từng dòng.
    ActivityDispatcher sẽ thực hiện các Activity con trên từng phần tử.
    """

    PARAMETERS = {
        "data": {
            "type": "array",
            "description": "Danh sách dữ liệu cần lặp."
        }
    }

    EXAMPLES = [
        "Lặp qua danh sách nhân viên",
        "Duyệt từng dòng Excel",
        "For each row in table"
    ]

    @staticmethod
    def execute(data):
        return [
            {
                "index": index,
                "item": row
            }
            for index, row in enumerate(data)
        ]