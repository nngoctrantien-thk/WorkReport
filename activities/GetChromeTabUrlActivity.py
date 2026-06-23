from activities.BaseActivity import BaseActivity
from service.ChromeManager import ChromeManager


class GetChromeTabUrlActivity(BaseActivity):

    NAME = "GetChromeTabUrlActivity"
    DESCRIPTION = """
    Lấy đường dẫn (URL) chính xác của một tab Chrome cụ thể dựa vào lịch sử quét 
    và lưu vào bộ nhớ tạm (context) để các lệnh sau có thể tái sử dụng.
    """

    PARAMETERS = {
        "index": {
            "type": "integer",
            "description": "Số thứ tự của tab cần lấy URL (1, 2, 3...).",
            "required": False,
            "default": None
        },
        "keyword": {
            "type": "string",
            "description": "Từ khóa trong tiêu đề để tìm tab cần lấy URL.",
            "required": False,
            "default": None
        },
        "remote_port": {
            "type": "integer",
            "description": "Cổng Debug của Chrome",
            "required": False,
            "default": 9222
        }
    }

    @staticmethod
    def execute(context=None, index=None, keyword=None, remote_port=9222, **kwargs):
        user_id = kwargs.get("user_id", "global")
        
        manager = ChromeManager(context=context, remote_port=remote_port, user_id=user_id)
        
        target_tab, error_msg = manager.find_tab_by_target(index=index, keyword=keyword)
        if error_msg:
            return error_msg

        url = manager.get_tab_url(target_tab)

        if not url:
            return f"❌ Tìm thấy tab *{target_tab.title}* nhưng không thể trích xuất được đường dẫn URL."

        if context is not None:
            context["last_extracted_url"] = url

        return (
            f"🔗 ĐƯỜNG DẪN TAB CHROME\n"
            f"📌 *Tab:* {target_tab.title}\n"
            f"🌐 *URL:* {url}\n"
            f"💾 *Trạng thái:* Đã lưu vào bộ nhớ luồng để sẵn sàng mở trình duyệt!"
        )