import os
from utils.llm_service import LlmService # Giả định file llm_service.py nằm cùng thư mục
from dotenv import load_dotenv
load_dotenv()
# --- CẤU HÌNH ---
# Nên lấy từ biến môi trường, nhưng để test nhanh ta dùng os.getenv()
# Đảm bảo bạn đã tạo file .env và chạy 'load_dotenv()' trong main.py/hoặc trước khi chạy test này
MY_API_KEY = os.getenv("GEMINI_API_KEY") 

def main():
    print("--- KHỞI TẠO LLM SERVICE ---")
    if not MY_API_KEY:
        print("❌ LỖI: Vui lòng set biến môi trường GEMINI_API_KEY với API Key thật.")
        return
        
    try:
        # Khởi tạo LlmService đã được sửa (chỉ trả về string)
        llm = LlmService(api_key=MY_API_KEY)
    except Exception as e:
        print(f"❌ Lỗi khởi tạo LlmService: {e}")
        return

    while True:
        print("\n" + "="*70)
        query = input("Nhập query TIẾNG VIỆT (hoặc 'exit' để thoát): ")
        if query.lower() in ['exit', 'quit']:
            break
            
        print(f"⏳ Đang gửi query gốc: '{query}' tới Gemini...")
        
        # Gọi hàm mới (chỉ trả về một string)
        refined_query = llm.refine_for_clip(query)
        
        print("\n✅ KẾT QUẢ REPROMPT (Tối ưu cho CLIP/Vector Search):")
        print(f"-> QUERY GỐC: {query}")
        print(f"-> QUERY REFINED: {refined_query}")
        
        if refined_query != query:
            print("🌟 Reprompt thành công! Sử dụng chuỗi tiếng Anh này để search FAISS.")
        else:
            print("⚠️ Reprompt không thành công hoặc không cần thiết. Đã trả về query gốc.")


if __name__ == "__main__":
    # Load .env (cần thiết nếu bạn dùng os.getenv)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Đã load file .env.")
    except ImportError:
        print("Không tìm thấy thư viện 'python-dotenv'. Đang sử dụng Key cứng hoặc biến môi trường đã có.")
        
    main()