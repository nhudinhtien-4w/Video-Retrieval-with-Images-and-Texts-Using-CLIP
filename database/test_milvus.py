from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection,
    utility
)
import random

# --- BƯỚC 1: KẾT NỐI ---
print("1. Đang kết nối tới Milvus...")
connections.connect("default", host="localhost", port="19530")

print("Các collection hiện có:", utility.list_collections())

# --- BƯỚC 2: ĐỊNH NGHĨA SCHEMA (CẤU TRÚC) ---
# Tưởng tượng ta đang lưu các đoạn văn bản.
# 1. ID: Số nguyên, khóa chính
# 2. embedding: Vector đại diện cho văn bản (giả sử vector có 8 chiều)
# 3. content: Nội dung văn bản gốc (để đọc hiểu)

fields = [
    FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=8), # Vector 8 chiều
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=200)
]

schema = CollectionSchema(fields, description="Demo Milvus cơ bản")

# --- BƯỚC 3: TẠO COLLECTION ---
collection_name = "hello_milvus"

# Nếu đã có thì xóa đi làm lại cho sạch
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)

collection = Collection(name=collection_name, schema=schema)
print(f"2. Đã tạo Collection: {collection_name}")




# --- BƯỚC 4: INSERT DỮ LIỆU GIẢ ---
# Tạo 10 vector ngẫu nhiên
data = [
    [i for i in range(10)], # Cột pk (0 đến 9)
    [[random.random() for _ in range(8)] for _ in range(10)], # Cột embedding (10 vector, mỗi cái 8 chiều)
    [f"Đây là văn bản số {i}" for i in range(10)] # Cột content
]

collection.insert(data)
print("3. Đã insert 10 entities.")

# --- BƯỚC 5: TẠO INDEX (CHỈ MỤC) ---
# Index giúp tìm kiếm nhanh hơn. Nếu không có index, Milvus sẽ quét toàn bộ (brute-force).
index_params = {
    "metric_type": "L2",       # L2: Khoảng cách Euclid (càng nhỏ càng giống)
    "index_type": "IVF_FLAT",  # Một loại index phổ biến
    "params": {"nlist": 128}
}

collection.create_index(field_name="embedding", index_params=index_params)
print("4. Đã tạo Index xong.")

# --- BƯỚC 6: LOAD COLLECTION (QUAN TRỌNG NHẤT) ---
# Milvus tách biệt lưu trữ và tính toán. Muốn search phải load lên RAM.
collection.load()
print("5. Đã load collection lên RAM.")

# --- BƯỚC 7: TÌM KIẾM (SEARCH) ---
# Giả sử ta có 1 vector truy vấn (query vector) và muốn tìm top 3 cái giống nhất
query_vector = [[random.random() for _ in range(8)]] # 1 vector ngẫu nhiên

search_params = {
    "metric_type": "L2", 
    "params": {"nprobe": 10}
}

print("\n--- KẾT QUẢ TÌM KIẾM ---")
results = collection.search(
    data=query_vector, 
    anns_field="embedding", 
    param=search_params, 
    limit=3, # Top 3
    output_fields=["content"] # Trả về thêm cột content để xem
)

for hits in results:
    for hit in hits:
        print(f"ID: {hit.id}, Distance: {hit.distance:.4f}, Content: {hit.entity.get('content')}")

# --- DỌN DẸP (Tùy chọn) ---
# collection.release() # Giải phóng RAM nhưng giữ dữ liệu đĩa