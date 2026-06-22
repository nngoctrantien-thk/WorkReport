from activities.BaseActivity import BaseActivity
class SummarizeActivity(BaseActivity):

    @staticmethod
    def execute(html=None, image_path=None):

        prompt = f"""
Tóm tắt nội dung sau:

{html}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text