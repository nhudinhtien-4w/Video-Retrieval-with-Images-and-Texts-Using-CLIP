# import sys
# import os
# import torch
# import open_clip
# from pymilvus import connections, Collection

# # --- CẤU HÌNH ---
# # Phải khớp với lúc insert
# COLLECTION_NAME = 'video_search_vit_b_32' 
# MODEL_NAME = 'ViT-B-32'
# PRETRAINED = 'laion2b_s34b_b79k'

# def main():
#     # 1. Nhập câu truy vấn
#     query_text = input("👉 Nhập từ khóa tìm kiếm (Tiếng Anh): ")
#     if not query_text:
#         print("Vui lòng nhập gì đó...")
#         return

#     # 2. Load Model để mã hóa văn bản (Text Encoding)
#     print("⏳ Đang load model để hiểu văn bản...")
#     device = "cuda" if torch.cuda.is_available() else "cpu"
    
#     # Load model (chỉ cần phần text encoder)
#     model, _, _ = open_clip.create_model_and_transforms(
#         MODEL_NAME, pretrained=PRETRAINED, device=device
#     )
#     tokenizer = open_clip.get_tokenizer(MODEL_NAME)

#     # 3. Chuyển văn bản thành Vector
#     print(f"🔄 Đang chuyển '{query_text}' thành vector...")
#     with torch.no_grad():
#         text_tokens = tokenizer([query_text]).to(device)
#         text_features = model.encode_text(text_tokens)
        
#         # Chuẩn hóa vector (Quan trọng để tính khoảng cách chính xác)
#         text_features /= text_features.norm(dim=-1, keepdim=True)
        
#         # Chuyển sang list để gửi cho Milvus
#         query_vector = text_features.cpu().numpy()[0].tolist()

#     # 4. Kết nối Milvus và Search
#     print("🚀 Đang tìm trong Milvus...")
#     connections.connect("default", host="127.0.0.1", port="19530")
    
#     collection = Collection(COLLECTION_NAME)
#     collection.load() # Đảm bảo data đã ở trên RAM

#     # Cấu hình tìm kiếm
#     search_params = {
#         "metric_type": "L2", 
#         "params": {"nprobe": 10} # Tìm trong 10 cụm (tăng lên nếu muốn tìm kỹ hơn)
#     }

#     results = collection.search(
#         data=[query_vector], 
#         anns_field="embedding", 
#         param=search_params, 
#         limit=5, # Lấy Top 5 kết quả
#         output_fields=["video_id", "frame_id", "path"] # Lấy thêm thông tin để hiển thị
#     )

#     # 5. Hiển thị kết quả
#     print("\n" + "="*30)
#     print(f"KẾT QUẢ CHO: '{query_text}'")
#     print("="*30)
    
#     for hits in results:
#         for i, hit in enumerate(hits):
#             # Lấy thông tin
#             vid = hit.entity.get("video_id")
#             fid = hit.entity.get("frame_id")
#             path = hit.entity.get("path")
#             dist = hit.distance
            
#             print(f"Top {i+1} | Dist: {dist:.4f}")
#             print(f"   🎬 Video: {vid} - Frame: {fid}")
#             print(f"   📂 Path:  {path}")
#             print("-" * 20)

# if __name__ == "__main__":
#     main()



import sys
import os
import torch
import open_clip
from PIL import Image
import matplotlib.pyplot as plt # Thư viện vẽ ảnh
from pymilvus import connections, Collection

# --- CẤU HÌNH (Khớp với lúc Insert) ---
COLLECTION_NAME = 'video_search_vit_b_32'
MODEL_NAME = 'ViT-B-32'
PRETRAINED = 'laion2b_s34b_b79k'

def show_images(results):
    """Hàm vẽ Grid ảnh kết quả"""
    top_k = len(results[0])
    
    # Tạo khung hình (Figure)
    fig = plt.figure(figsize=(15, 6))
    plt.suptitle(f"Top {top_k} Results", fontsize=16)

    for i, hit in enumerate(results[0]):
        # Lấy thông tin
        path = hit.entity.get("path")
        dist = hit.distance
        video_id = hit.entity.get("video_id")
        
        # Xử lý đường dẫn (Nếu lưu tương đối thì cần nối với thư mục gốc)
        if not os.path.exists(path):
            # Thử fix đường dẫn nếu chạy từ thư mục khác
            path = os.path.join(os.getcwd(), path)
        
        # Tạo ô con (Subplot)
        ax = fig.add_subplot(1, top_k, i + 1)
        
        try:
            img = Image.open(path).convert('RGB')
            ax.imshow(img)
            # Đặt tiêu đề cho từng ảnh
            ax.set_title(f"Rank {i+1}\nDist: {dist:.3f}\n{video_id}", color='green', fontsize=10)
        except Exception as e:
            print(f"Không load được ảnh: {path}")
            ax.text(0.5, 0.5, "Image Not Found", ha='center', va='center')
        
        # Ẩn trục tọa độ cho đẹp
        ax.axis('off')

    # Hiển thị cửa sổ
    print("✅ Đang mở cửa sổ kết quả...")
    plt.tight_layout()
    plt.show()

def main():
    # 1. Nhập từ khóa
    query_text = input("👉 Nhập mô tả (Tiếng Anh): ")
    if not query_text: return

    # 2. Load Model Text Encoder
    print("⏳ Loading model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, _ = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED, device=device)
    tokenizer = open_clip.get_tokenizer(MODEL_NAME)

    # 3. Encode Text
    with torch.no_grad():
        text_features = model.encode_text(tokenizer([query_text]).to(device))
        text_features /= text_features.norm(dim=-1, keepdim=True)
        query_vector = text_features.cpu().numpy()[0].tolist()

    # 4. Search Milvus
    connections.connect("default", host="127.0.0.1", port="19530")
    collection = Collection(COLLECTION_NAME)
    collection.load()

    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    
    # Lấy Top 5 kết quả
    results = collection.search(
        data=[query_vector], 
        anns_field="embedding", 
        param=search_params, 
        limit=15, 
        output_fields=["path", "video_id"]
    )

    # 5. Hiển thị ảnh
    show_images(results)

if __name__ == "__main__":
    main()