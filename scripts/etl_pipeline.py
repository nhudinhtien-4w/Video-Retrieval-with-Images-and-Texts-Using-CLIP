import sys
import os
import json
from tqdm import tqdm
from pathlib import Path

# Import module của mình
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.milvus_db import MilvusDB
from database.feature_extractor import FeatureExtractor

# # CẤU HÌNH
JSON_PATH = 'data/index/path_index_clip.json'

# MODEL_NAME = 'ViT-H-14-378-quickgelu' 
MODEL_NAME = 'ViT-B-32' 
# PRETRAINED = 'dfn5b'
PRETRAINED = 'laion2b_s34b_b79k'
safe_model_name = MODEL_NAME.replace("-", "_").replace("/", "_")
COLLECTION = f"video_search_v2_{safe_model_name}"

def parse_video_info(file_path):
    try:
        path_obj = Path(file_path)
        # data/keyframe/L01_V001/0001.jpg
        video_id = path_obj.parent.name # Lấy tên folder cha (L01_V001)
        
        # Lấy frame id từ tên file (bỏ đuôi mở rộng)
        stem = path_obj.stem # "keyframe_0001"
        frame_id_str = stem.replace("keyframe_", "")
        frame_id = int(frame_id_str)
        
        return video_id, frame_id
    except:
        return "Unknown", 0

def main():
    # 1. Load Model
    extractor = FeatureExtractor(model_name=MODEL_NAME, pretrained=PRETRAINED)
    dim = extractor.get_dim()
    
    # 2. Setup Milvus
    milvus = MilvusDB(dim=dim, collection_name=COLLECTION)
    milvus.create_collection(recreate=True) 

    # 3. Load Data List
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    # 4. ETL Loop
    batch_size = 64
    batch_buffer = []
    
    # items = list(data.items())
    # Test trước 10000 keyframe
    items = list(data.items())[:100000]

    print(f"Processing {len(items)} images...")
    
    for key, path in tqdm(items):
        full_path = path if os.path.exists(path) else os.path.join(os.getcwd(), path)
        if not os.path.exists(full_path):
            continue
            
        # Extract Vector
        embedding = extractor.encode_image(full_path)
        if embedding is None:
            continue
            
        # Parse Metadata
        video_id, frame_id = parse_video_info(path)
        
        # Add to buffer
        batch_buffer.append({
            'id': int(key),
            'video_id': video_id,
            'frame_id': frame_id,
            'path': path,
            'embedding': embedding
        })
        
        # Flush if full
        if len(batch_buffer) >= batch_size:
            milvus.insert_batch_data(batch_buffer)
            batch_buffer = []
            
    # Insert remaining
    if batch_buffer:
        milvus.insert_batch_data(batch_buffer)
    
    # 5. Build Index 
    print("Building HNSW Index...")
    milvus.create_index()
    print("DONE!")

if __name__ == "__main__":
    main()



import sys
import os
import json
import pickle # Thư viện để lưu file tạm
from tqdm import tqdm
from pathlib import Path

# Import module của mình
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from database.milvus_db import MilvusDB # <--- Tạm thời không cần cái này
from database.feature_extractor import FeatureExtractor

# CẤU HÌNH
JSON_PATH = 'data/index/path_index_clip.json'
SAVE_FILE = 'vectors_dump_quickgelu.pkl' # Tên file lưu tạm

# --- HÀM BỊ THIẾU (PHẢI CÓ CÁI NÀY MỚI CHẠY ĐƯỢC) ---
def parse_video_info(file_path):
    try:
        path_obj = Path(file_path)
        # Giả định path: data/keyframe/L01_V001/0001.jpg
        video_id = path_obj.parent.name # Lấy folder cha (L01_V001)
        
        # Lấy frame id
        stem = path_obj.stem # "keyframe_0001" hoặc "0001"
        # Xử lý linh hoạt: nếu tên file có chữ keyframe_ thì xóa đi
        frame_id_str = stem.replace("keyframe_", "") 
        frame_id = int(frame_id_str)
        
        return video_id, frame_id
    except:
        return "Unknown", 0

# MODEL_NAME = 'ViT-H-14-378-quickgelu' 
# PRETRAINED = 'dfn5b'

def main():
    # 1. Load Model (Dùng bản nhẹ ViT-B-32 để chạy nhanh trên CPU)
    # Lưu ý: Nếu bạn chưa sửa file feature_extractor.py để nhận tham số này thì cứ giữ mặc định
    try:
        extractor = FeatureExtractor(model_name='ViT-B-32', pretrained='laion2b_s34b_b79k')
    except:
        # Fallback nếu code cũ của bạn hard-code model
        print("Cảnh báo: Không load được ViT-B-32, đang dùng model mặc định trong code...")
        extractor = FeatureExtractor()

    # 2. KHÔNG KẾT NỐI MILVUS LÚC NÀY
    print("--- CHẾ ĐỘ: CHỈ TRÍCH XUẤT (NO DB) ---")

    # 3. Load Data List
    if not os.path.exists(JSON_PATH):
        print(f"Lỗi: Không tìm thấy file {JSON_PATH}")
        return

    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    # Test trước 10000 keyframe (hoặc bỏ [:10000] nếu muốn chạy hết)
    items = list(data.items())[:10000]

    # Chuẩn bị list chứa
    saved_vectors = [] 
    
    print(f"Đang xử lý {len(items)} ảnh trên CPU...")
    
    # 4. Vòng lặp ETL
    for key, path in tqdm(items):
        # Xử lý đường dẫn tuyệt đối/tương đối
        full_path = path if os.path.exists(path) else os.path.join(os.getcwd(), path)
        if not os.path.exists(full_path):
            continue
            
        # Trích xuất Vector
        embedding = extractor.encode_image(full_path)
        if embedding is None:
            continue
            
        # Lấy thông tin phụ
        video_id, frame_id = parse_video_info(path)
        
        # Lưu vào RAM
        saved_vectors.append({
            'id': int(key),
            'video_id': video_id,
            'frame_id': frame_id,
            'path': path,
            'embedding': embedding
        })

        # Cứ mỗi 1000 ảnh thì lưu đè ra file 1 lần (Checkpoint)
        # Để lỡ máy có sập thì còn giữ được tiến độ
        if len(saved_vectors) % 1000 == 0:
            with open(SAVE_FILE, 'wb') as f:
                pickle.dump(saved_vectors, f)

    # 5. Lưu lần cuối cùng khi chạy xong
    with open(SAVE_FILE, 'wb') as f:
        pickle.dump(saved_vectors, f)
    
    print(f"\n✅ XONG GIAI ĐOẠN 1!")
    print(f"Dữ liệu đã lưu tại: {SAVE_FILE}")
    print(f"Tổng số vector: {len(saved_vectors)}")
    print("Bây giờ bạn có thể bật Docker lên và chạy script insert.")

if __name__ == "__main__":
    main()