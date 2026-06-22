from activities.BaseActivity import BaseActivity
class ScreenshotActivity(BaseActivity):

    NAME = "ScreenshotActivity"

    @staticmethod
    def execute(driver, path="screenshot.png", **kwargs):

        driver.save_screenshot(path)

        return path