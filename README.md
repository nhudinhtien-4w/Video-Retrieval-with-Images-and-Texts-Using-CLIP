# IR-Phat - Video Information Retrieval System

Hệ thống truy vấn thông tin video sử dụng kết hợp các công nghệ tiên tiến:
- **CLIP (OpenAI/OpenCLIP)**: Trích xuất đặc trưng hình ảnh và văn bản.
- **Elasticsearch**: Tìm kiếm văn bản và metadata.
- **Gemini LLM**: Hỗ trợ xử lý ngôn ngữ tự nhiên và sinh câu trả lời.
- **FastAPI**: Backend framework.

### 2. Cài đặt thư viện
pip install -r requirements.txt

### 3. Chuẩn bị dữ liệu
gdown --folder https://drive.google.com/file/d/1o0z-M755ziojL-rx1gQDVOkZo6yhMwrQ/view?usp=drive_link -O data/bin

gdown --folder https://drive.google.com/file/d/1LIMAsaEb75RVRpRongYJcZo1tN9ul6E7/view?usp=sharing -O data/clip_frame

gdown --folder https://drive.google.com/file/d/1ddC8S358SVDznE1pwlxZBbmmjG8sdCBF/view?usp=sharing -O data/mid_frame

##  Khởi chạy ứng dụng
Chạy es: 
Mở docker: 
docker compose up -d

Chạy server FastAPI:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload


Truy cập vào: http://localhost:8000

##  Cấu trúc dự án
- main.py\: Entry point của ứng dụng FastAPI.
- configs.py\: Các cấu hình hệ thống.
- database\: Cấu hình và scripts cho Milvus/Docker.
- utils\: Các module tiện ích (FAISS, Elasticsearch, LLM, ...).
- scripts\: Các script hỗ trợ (ETL, download data, ...).
- 	emplates\ & static\: Giao diện Web.

##  Notes
- Hệ thống mặc định đang sử dụng CLIP ViT-L/14, nếu muốn sử dụng model khác, hãy tinh chỉnh trong file config.py.
- Hệ thống được lên ý tưởng và cải tiến từ nguồn: https://github.com/chisngooo/Multimodal-Video-Retrieval-Engine-with-Vision-and-Text.git
