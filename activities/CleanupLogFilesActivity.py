from pathlib import Path
from datetime import datetime, timedelta

from config import LOG_DIRECTORY


class CleanupLogFilesActivity:

    NAME = "CleanupLogFilesActivity"

    DESCRIPTION = """
    Xóa các file log cũ.
    """

    PARAMETERS = {
        "retention_days": {
            "type": "integer",
            "description": "Số ngày giữ lại log.",
            "default": 7
        },
        "log_directory": {
            "type": "string",
            "description": "Đường dẫn thư mục log.",
            "default": LOG_DIRECTORY
        },
        "pattern": {
            "type": "string",
            "default": "*.log"
        }
    }

    EXAMPLES = [
        "xóa log",
        "cleanup log",
        "xóa log 30 ngày",
        "delete old logs"
    ]

    @staticmethod
    def execute(
        retention_days=7,
        log_directory=LOG_DIRECTORY,
        pattern="*.log"
    ):

        log_dir = Path(log_directory)

        if not log_dir.exists():
            return "Log directory not found."

        cutoff = datetime.now() - timedelta(days=retention_days)

        deleted = 0

        for file in log_dir.glob(pattern):

            if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:

                try:
                    file.unlink()
                    deleted += 1
                except Exception:
                    pass

        return f"Deleted {deleted} log files."