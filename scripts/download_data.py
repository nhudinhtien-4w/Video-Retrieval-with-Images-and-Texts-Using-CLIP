import gdown
import os
import zipfile

def download_data():
    # Thay thế ID bên dưới bằng ID file Google Drive của bạn
    # Ví dụ: file_id = '1-xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx'
    # Nếu là folder, hãy nén lại thành zip trước khi upload lên Drive
    
    file_id = 'YOUR_GOOGLE_DRIVE_FILE_ID_HERE'
    output = 'data_bin.zip'
    
    if file_id == 'YOUR_GOOGLE_DRIVE_FILE_ID_HERE':
        print("Vui lòng cập nhật FILE_ID trong scripts/download_data.py trước khi chạy!")
        return

    url = f'https://drive.google.com/uc?id={file_id}'
    
    if not os.path.exists('data'):
        os.makedirs('data')
        
    print(f"Đang tải xuống dữ liệu từ Google Drive (ID: {file_id})...")
    gdown.download(url, output, quiet=False)
    
    print("Đang giải nén...")
    with zipfile.ZipFile(output, 'r') as zip_ref:
        zip_ref.extractall('data/')
        
    print("Hoàn tất! Đã xóa file zip.")
    os.remove(output)

if __name__ == "__main__":
    download_data()
