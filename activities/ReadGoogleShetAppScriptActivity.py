import requests

class ReadGoogleSheetAppScriptActivity:
    @staticmethod
    def read_range(api_url: str):
        """
        Gọi API từ Google Apps Script Web App để lấy dữ liệu dạng Danh sách các Dictionary.
        """
        try:
            response = requests.get(api_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Kết nối thất bại. Mã phản hồi HTTP: {response.status_code}")
                
        except requests.exceptions.JSONDecodeError:
            print("\n" + "="*50)
            print("🚨 LỖI PHÂN QUYỀN APPS SCRIPT:")
            print("Google đang trả về trang HTML bắt Đăng nhập chứ không trả về dữ liệu.")
            print("Vui lòng Deploy lại Web App với quyền truy cập là 'Anyone'.")
            print("="*50 + "\n")
            raise Exception("Dữ liệu phản hồi từ Google không đúng định dạng JSON.")
            
        except Exception as e:
            raise Exception(f"Lỗi hệ thống khi gọi AppScript API: {str(e)}")