import requests


class GoogleAppSheetAPI:

    def __init__(self):
        self.access_key = None
        self.app_id = None
        self.base_url = None

    def authenticate(self, access_key, app_id):
        self.access_key = access_key
        self.app_id = app_id

        self.base_url = (
            f"https://api.appsheet.com/api/v2/apps/{app_id}/tables"
        )

    def read_range(self, table_name):
        url = f"{self.base_url}/{table_name}/Action"

        headers = {
            "ApplicationAccessKey": self.access_key,
            "Content-Type": "application/json"
        }

        payload = {
            "Action": "Find",
            "Properties": {},
            "Rows": []
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )


        print("Status:", response.status_code)
        print("Response:", response.text)

        response.raise_for_status()

        return response.json()

    def add_row(self, table_name, data):
        url = f"{self.base_url}/{table_name}/Action"

        headers = {
            "ApplicationAccessKey": self.access_key,
            "Content-Type": "application/json"
        }

        payload = {
            "Action": "Add",
            "Properties": {},
            "Rows": [data]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    def update_row(self, table_name, data):
        url = f"{self.base_url}/{table_name}/Action"

        headers = {
            "ApplicationAccessKey": self.access_key,
            "Content-Type": "application/json"
        }

        payload = {
            "Action": "Edit",
            "Properties": {},
            "Rows": [data]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    def delete_row(self, table_name, key_value, key_column="ID"):
        url = f"{self.base_url}/{table_name}/Action"

        headers = {
            "ApplicationAccessKey": self.access_key,
            "Content-Type": "application/json"
        }

        payload = {
            "Action": "Delete",
            "Properties": {},
            "Rows": [
                {
                    key_column: key_value
                }
            ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        return response.json()