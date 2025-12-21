import pickle
import time
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection,
    utility
)

# --- CẤU HÌNH ---
PKL_FILE = 'vectors_dump.pkl'
COLLECTION_NAME = 'video_search_vit_b_32' # Đặt tên rõ ràng
DIMENSION = 512  # ViT-B-32 có vector size là 512
BATCH_SIZE = 1000 # Insert từng cục 1000 dòng

def main():
    # 1. Kết nối Milvus
    print("1. Đang kết nối tới Milvus...")
    try:
        connections.connect("default", host="127.0.0.1", port="19530")
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
        print("Hãy chắc chắn bạn đã chạy 'docker compose start'!")
        return

    # 2. Đọc dữ liệu từ file PKL
    print(f"2. Đang đọc file {PKL_FILE}...")
    with open(PKL_FILE, 'rb') as f:
        data = pickle.load(f)
    print(f"-> Đã load {len(data)} dòng dữ liệu.")

    # 3. Chuẩn bị dữ liệu theo cột (Milvus yêu cầu Column-based)
    # File pkl đang là list of dicts, cần chuyển thành list of lists
    ids = [item['id'] for item in data]
    video_ids = [str(item['video_id']) for item in data]
    frame_ids = [int(item['frame_id']) for item in data]
    paths = [str(item['path']) for item in data]
    embeddings = [item['embedding'] for item in data]

    # Kiểm tra chiều dài vector xem có đúng 512 không
    if len(embeddings) > 0 and len(embeddings[0]) != DIMENSION:
        print(f"❌ LỖI DIMENSION! Config là {DIMENSION} nhưng dữ liệu là {len(embeddings[0])}")
        return

    # 4. Tạo Collection (Xóa cũ nếu có)
    if utility.has_collection(COLLECTION_NAME):
        print(f"Phát hiện collection cũ '{COLLECTION_NAME}', đang xóa...")
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="video_id", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="frame_id", dtype=DataType.INT64),
        FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION)
    ]
    schema = CollectionSchema(fields, description="Video Retrieval Collection")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    print(f"3. Đã tạo Collection mới: {COLLECTION_NAME}")

    # 5. Insert dữ liệu (Chia nhỏ để insert cho an toàn)
    print("4. Bắt đầu Insert...")
    total = len(data)
    
    # Gom các cột lại thành 1 cục lớn
    entities = [ids, video_ids, frame_ids, paths, embeddings]
    
    start_time = time.time()
    collection.insert(entities)
    end_time = time.time()
    
    print(f"-> Insert xong {total} dòng trong {end_time - start_time:.2f} giây.")

    # 6. Tạo Index (Bắt buộc để search nhanh)
    print("5. Đang tạo Index (IVF_FLAT)...")
    index_params = {
        "metric_type": "L2", # Hoặc COSINE tùy model, CLIP thường dùng COSINE hoặc L2 (sau khi normalize) đều ổn
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print("-> Index xong!")

    # 7. Load lên RAM để sẵn sàng search
    collection.load()
    print("\n✅ HOÀN TẤT! Hệ thống đã sẵn sàng để search.")
    print(f"Số lượng entities trong Milvus: {collection.num_entities}")

if __name__ == "__main__":
    main()