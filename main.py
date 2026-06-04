import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from activities import *
from common import Common
from service import Service

today = datetime.now().strftime("%Y-%m-%d")
#today = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
user_name = "Nguyen Ngoc Tran Tien"
url = f"https://work-report.thk-hd-hn.vn/report?team_id=2&user_id=&start_date={today}&end_date={today}"

profile_path = r"C:\chrome-selenium-profile"
if not os.path.exists(profile_path):
    os.makedirs(profile_path)

driver = None
id_models = 'createReportModal'
# createReportModal | editReportModal
try:
    driver = OpenBrowserActivity.execute(url=url, profile_path=profile_path, headless=True)
    common = Common(driver)
    service = Service(common)
    
    common.log("Starting the automation process.")
    common.log("Browser opened successfully.")
    common.log(f"Title: {driver.title} | URL: {driver.current_url}")

    logged_in = False
    is_login_btn_exists = common.wait_exists("//button[text()='Login']", retry=3, sleep=2)
    
    if is_login_btn_exists:
        common.log("Login button exists. Proceeding with login...")
        common.input("//input[@name='email']", "n_ngoctrantien")
        common.input("//input[@name='password']", "25081996Asd@")
        common.click("//button[text()='Login']")
        DelayActivity.execute(5)
        
        if common.exists("//a[normalize-space()='Create Report']"):
            common.log("Logged in successfully via Form.")
            logged_in = True
        else:
            raise Exception("Login clicked but 'Create Report' button not found.")
    else:
        if common.exists("//a[normalize-space()='Create Report']"):
            common.log("Already logged in via existing Chrome Profile Session.")
            logged_in = True
        else:
            raise Exception("Neither Login button nor Create Report button exists. Check page state!")

    if logged_in:
        excel = ExcelActivity(r"C:\Users\pc\Desktop\WorkReport.xlsx")
        data = excel.read_range("WRP", None, True)
        common.log(f"Data rows loaded from Excel: {len(data)}")
        user_report_xpath = f"//tr[td[normalize-space()='{user_name}']]//div[contains(@class,'report-col-content')]"
        
        if common.exists(user_report_xpath):
            common.click(user_report_xpath)
            common.log(f"Opened report modal for user: {user_name}")
            DelayActivity.execute(5)
            # get id_models
            if Service.get_id_model(service) not in ["", None]:
                id_models = 'editReportModal'
            common.log(f"Report modal ID : {id_models}")
            for index, row in ForEachDataTableActivity.execute(data):
                common.log(f"Processing Excel row index: {index}")
                
                select_task_today = row.get("select_task_today", "")
                task_details_today = row.get("task_details_today", "")
                task_hours_today = row.get("task_hours_today", 0)

                select_task_tomorrow = row.get("select_task_tomorrow", "")
                task_details_tomorrow = row.get("task_details_tomorrow", "")
                task_hours_tomorrow = row.get("task_hours_tomorrow", 0)

                if index > 0:
                    if service.safe(select_task_today) not in ["", None]:
                        common.click("//button[contains(@class,'btn-add-today-task')]")
                        common.log("Added a new row for Today's task.")
                        
                    if service.safe(select_task_tomorrow) not in ["", None]:
                        common.log(f"Next task tomorrow found: {service.safe(select_task_tomorrow)}")
                        common.click("//button[contains(@class,'btn-add-tomorrow-task')]")
                        common.log("Added a new row for Tomorrow's task.")
                
                service.sequence_tasks(
                    select_task_today, task_details_today, task_hours_today, 
                    select_task_tomorrow, task_details_tomorrow, task_hours_tomorrow, 
                    index
                )
            
            common.click(f"//div[@id='{id_models}']//button[text()='Save Report']")
            common.log("Click 'Save Report' button executed.")
            service.click_ok_if_exists()
        else:
            common.log(f"Could not find the report cell for user '{user_name}' on the webpage table.")

    DelayActivity.execute(3)
    common.log("Script executed completed successfully.")

except Exception as e:
    common.log(f"CRITICAL ERROR during automation: {str(e)}")

finally:
    if driver:
        driver.quit()
        print("Browser closed cleanly via finally block.")