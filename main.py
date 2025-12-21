import logging
from contextlib import asynccontextmanager
from typing import Optional, List
from urllib.parse import unquote
import io
import base64

from fastapi import FastAPI, Request, Query, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch, os
from PIL import Image
import numpy as np

# --- IMPORT MODULES CỦA HỆ THỐNG MỚI ---
from configs import MODEL_CONFIGS          # File cấu hình
from utils.faiss_service import FaissService # Service xử lý Vector/CLIP
from utils.es_service import EsService       # Service xử lý Elasticsearch
from utils.llm_service import LlmService
from utils.query_processing import Translation
from utils.multi_context_kis import MultiContextKIS  # Multi-Context KIS

from dotenv import load_dotenv
load_dotenv()

# Import submit module
from submit import full_submission_flow


# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# 1. GLOBAL VARIABLES (QUẢN LÝ TRẠNG THÁI)
# ==========================================
# Dictionary chứa các FaissService đã load (Key là ID trong config)
faiss_services = {} 

# Biến chứa EsService (chỉ cần 1 instance)
es_service = None

# Multi-Context KIS service
multi_context_kis = None

# ==========================================
# 2. LIFESPAN (KHỞI ĐỘNG & DỌN DẸP SERVER)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("========== SERVER STARTING ==========")
    
    # 1. Khởi tạo Translator (Dùng chung cho tất cả)
    logger.info("Init Translator...")
    translator = Translation(from_lang='vi', to_lang='en', mode='google')
    
    # 2. Khởi tạo Elasticsearch Service (Nếu có)
    global es_service
    logger.info("Init Elasticsearch Service...")
    try:
        es_service = EsService(
            host="http://localhost:9200", 
            json_path="data/index/path_index_clip.json" 
        )
    except Exception as e:
        logger.error(f"Failed to init ES Service: {e}")

    # 3. Load các Model FAISS/CLIP theo Config
    loaded_count = 0
    for model_id, config in MODEL_CONFIGS.items():
        if config["enabled"]:
            try:
                logger.info(f"⏳ Loading Model ID {model_id}: {config['name']}...")
                
                # Kiểm tra file tồn tại
                import os
                if not os.path.exists(config["bin_path"]):
                    logger.warning(f"File bin không tồn tại: {config['bin_path']}. Bỏ qua.")
                    continue

                # Khởi tạo Service
                faiss_services[model_id] = FaissService(
                    bin_path=config["bin_path"],
                    json_path=config["json_path"],
                    model_type=config["type"],
                    model_name=config["model_key"],
                    device="cuda" if torch.cuda.is_available() else "cpu",
                    translator=translator,
                    pretrained=config.get("pretrained")  # Lấy pretrained từ config nếu có
                )
                logger.info(f"Loaded {config['name']} SUCCESS.")
                loaded_count += 1
            except Exception as e:
                logger.error(f"FAILED to load {config['name']}: {e}")
        else:
            logger.info(f"Skipped {config['name']} (Disabled)")
            
    logger.info(f"========== SYSTEM READY. Services loaded: {loaded_count} ==========")
    
    # # Init LLM Service
    global llm_service
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
    
    logger.info("Init LLM Service...")
    llm_service = LlmService(api_keys=GEMINI_API_KEY)

    # Init Multi-Context KIS Service
    global multi_context_kis
    if 6 in faiss_services:  # Sử dụng model ID 6 (ViT-L/14@336px)
        logger.info("Init Multi-Context KIS Service with ViT-L/14...")
        multi_context_kis = MultiContextKIS(
            faiss_service=faiss_services[6],
            es_service=es_service
        )
    elif len(faiss_services) > 0:
        # Fallback: Dùng model đầu tiên
        first_model_id = next(iter(faiss_services))
        logger.info(f"Init Multi-Context KIS with model ID {first_model_id}...")
        multi_context_kis = MultiContextKIS(
            faiss_service=faiss_services[first_model_id],
            es_service=es_service
        )

    logger.info(f"========== SYSTEM READY. Services loaded: {loaded_count} ==========")


    yield # Server chạy và chờ request tại đây
    
    # --- SHUTDOWN ---
    logger.info("========== SERVER STOPPING ==========")
    faiss_services.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# Khởi tạo App
app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/static", StaticFiles(directory="static"), name="static") 
if os.path.exists("image"):
    app.mount("/image", StaticFiles(directory="image"), name="image")
templates = Jinja2Templates(directory="templates")

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
class QueryParams(BaseModel):
    query: Optional[str] = Query(None)
    page: int = Query(1, ge=1)
    imgid: Optional[int] = Query(None)
    faiss: int = Query(7) # Mặc định ID 7 (ViT-B/32)

def paginate(data_list, page, limit=100):
    """Hàm cắt list dữ liệu theo trang"""
    if not data_list:
        return [], 1, 1, 0
        
    total_items = len(data_list)
    num_pages = (total_items // limit) + (1 if total_items % limit > 0 else 0)
    
    # Đảm bảo page hợp lệ
    page = max(1, min(page, num_pages)) if num_pages > 0 else 1
    
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    return data_list[start_idx:end_idx], page, num_pages, total_items

# ==========================================
# 4. API ENDPOINTS
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, params: QueryParams = Depends()):
    """
    Trang chủ: Hiển thị danh sách ảnh.
    Logic: Lấy danh sách ảnh từ model đang hoạt động đầu tiên.
    """
    # 1. Tìm một service bất kỳ đang hoạt động để lấy danh sách ảnh làm gốc
    active_service = None
    if 7 in faiss_services: # Ưu tiên ID 7 (B32)
        active_service = faiss_services[7]
    elif len(faiss_services) > 0: # Lấy cái đầu tiên nếu 7 tắt
        active_service = faiss_services[next(iter(faiss_services))]
    
    # Trạng thái các model để hiển thị UI
    available_models_status = {cfg["name"]: (k in faiss_services) for k, cfg in MODEL_CONFIGS.items()}

    if not active_service:
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "data": [],
            "page": 1, "num_pages": 1,
            "error_message": "Chưa có Model nào được bật (Enabled) hoặc Load thành công!",
            "available_models": available_models_status
        })

    # 2. Lấy toàn bộ ảnh từ id_map của service
    all_images = [{"id": k, "imgpath": f"/{v}"} for k, v in active_service.id_map.items()]
    
    # 3. Lọc theo video (Logic cũ)
    filter_video = request.query_params.get("video", None)
    if filter_video:
        all_images = [img for img in all_images if filter_video in img["imgpath"]]
        all_images.sort(key=lambda x: x["id"])
    else:
        # Nếu không lọc, chỉ lấy 2000 ảnh đầu để demo cho nhẹ trang chủ
        all_images = sorted(all_images, key=lambda x: x["id"])[:2000]

    # 4. Phân trang
    paginated_data, current_page, num_pages, total = paginate(all_images, params.page)

    # 5. Lấy danh sách tên video cho Dropdown
    # (Optional: Nếu muốn tối ưu có thể cache cái này lại)
    available_videos = set()
    for img in all_images[:5000]: # Sample 5000 ảnh để lấy prefix
        path = img["imgpath"]
        # Path format: /data/clip_frame/L24_V001/keyframe_xxx.webp
        parts = path.strip('/').split('/')  # Remove leading / and split
        if len(parts) >= 3 and parts[0] == 'data':
            available_videos.add(parts[2])  # Get video ID like L24_V001
            
    return templates.TemplateResponse("home.html", {
        "request": request,
        "data": paginated_data,
        "page": current_page,
        "num_pages": num_pages,
        "available_models": available_models_status,
        "available_videos": sorted(list(available_videos)),
        "filter_video": filter_video,
        "result_count": total
    })

@app.get("/clip", response_class=HTMLResponse)
async def text_search_api(request: Request, params: QueryParams = Depends()):
    """API Tìm kiếm Text-to-Image (CLIP)"""
    try:
        if not params.query:
            return templates.TemplateResponse("home.html", {
                "request": request, "data": [], "page": 1, "num_pages": 1, "error": "Vui lòng nhập từ khóa!"
            })

        # 1. Chọn Service
        service = faiss_services.get(params.faiss)
        if not service:
            return templates.TemplateResponse("home.html", {
                "request": request, "data": [], "page": 1, "num_pages": 1, 
                "error": f"Model ID {params.faiss} chưa được load."
            })

        # 2. Gọi hàm Search
        search_query = params.query
        if llm_service and llm_service.model:
            search_query = llm_service.refine_for_clip(params.query)
        logger.info(f"Final Search Query for CLIP: {search_query}")
        results = service.text_search(search_query, k=400)

        # 3. Phân trang
        paginated_data, current_page, num_pages, total = paginate(results, params.page)

        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": paginated_data,
            "page": current_page,
            "num_pages": num_pages,
            "query": params.query,
            "faiss": params.faiss,
            "search_type": "clip",
            "result_count": total
        })

    except Exception as e:
        logger.error(f"Lỗi API Clip: {e}")
        return templates.TemplateResponse("home.html", {"request": request, "data": [], "error": str(e)})

@app.post("/clip/image_search")
async def clip_image_search(
    request: Request,
    image: UploadFile = File(...),
    faiss: int = Form(...)
):
    """API tìm kiếm CLIP bằng hình ảnh"""
    try:
        # Load service
        service = faiss_services.get(faiss)
        if not service:
            return templates.TemplateResponse("home.html", {
                "request": request, 
                "data": [], 
                "page": 1,
                "num_pages": 1,
                "error": f"Model ID {faiss} chưa được load"
            })
        
        # Read and process image
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        
        # Encode image using CLIP
        with torch.no_grad():
            if hasattr(service, 'preprocess'):
                image_tensor = service.preprocess(pil_image).unsqueeze(0).to(service.device)
                
                if service.model_type == "open_clip":
                    features = service.model.encode_image(image_tensor)
                elif service.model_type == "openai":
                    features = service.model.encode_image(image_tensor)
                else:
                    return templates.TemplateResponse("home.html", {
                        "request": request,
                        "data": [],
                        "page": 1,
                        "num_pages": 1,
                        "error": "Model không hỗ trợ tìm kiếm bằng ảnh"
                    })
                
                vector = features.cpu().numpy().astype(np.float32)
                vector = vector / np.linalg.norm(vector, axis=1, keepdims=True)
                
                # Search in FAISS
                scores, ids = service.index.search(vector, 400)
                
                # Format results
                results = []
                for score, idx in zip(scores[0], ids[0]):
                    idx = int(idx)
                    if idx in service.id_map:
                        results.append({
                            "id": idx,
                            "score": float(score),
                            "imgpath": f"/{service.id_map[idx]}"
                        })
                
                # Paginate and return
                paginated_data, current_page, num_pages, total = paginate(results, 1)
                
                return templates.TemplateResponse("home.html", {
                    "request": request,
                    "data": paginated_data,
                    "page": current_page,
                    "num_pages": num_pages,
                    "query": "[Image Search]",
                    "faiss": faiss,
                    "search_type": "clip",
                    "result_count": total
                })
            else:
                return templates.TemplateResponse("home.html", {
                    "request": request,
                    "data": [],
                    "page": 1,
                    "num_pages": 1,
                    "error": "Model không hỗ trợ encode ảnh"
                })
                
    except Exception as e:
        logger.error(f"Error in image search: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": [],
            "page": 1,
            "num_pages": 1,
            "error": f"Lỗi tìm kiếm ảnh: {str(e)}"
        })

@app.get("/img", response_class=HTMLResponse)
async def image_search_api(request: Request, params: QueryParams = Depends()):
    """API Tìm kiếm Image-to-Image"""
    try:
        if params.imgid is None:
             return templates.TemplateResponse("home.html", {"request": request, "data": [], "error": "Thiếu ID ảnh!"})

        service = faiss_services.get(params.faiss)
        if not service:
            return templates.TemplateResponse("home.html", {"request": request, "data": [], "error": "Model chưa load."})

        # Gọi hàm Search
        results = service.image_search(params.imgid, k=400)

        # Phân trang
        paginated_data, current_page, num_pages, total = paginate(results, params.page)

        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": paginated_data,
            "page": current_page,
            "num_pages": num_pages,
            "imgid": params.imgid,
            "faiss": params.faiss,
            "search_type": "image",
            "result_count": total
        })
    except Exception as e:
        logger.error(f"Lỗi API Img: {e}")
        return templates.TemplateResponse("home.html", {"request": request, "data": [], "error": str(e)})

# ==========================================
# 5. API ELASTICSEARCH
# ==========================================

@app.get("/obj", response_class=HTMLResponse)
async def obj_api(request: Request, query: Optional[List[str]] = Query(None), params: QueryParams = Depends()):
    """Tìm kiếm Object Detection (Elasticsearch)"""
    if not es_service:
        return templates.TemplateResponse("home.html", {"request": request, "data": [], "error": "Elasticsearch chưa kết nối!"})
    
    # Parse query list từ URL: ["1 person", "2 car"] -> [(1, "person", "None"), ...]
    parsed_query = []
    if query:
        for item in query:
            # Giải mã URL (ví dụ: "1+person")
            parts = unquote(item).split()
            # Logic parse đơn giản: [quantity, name]
            if len(parts) >= 2:
                qty = parts[0]
                name = parts[1].replace("+", " ")
                parsed_query.append((qty, name, "None")) # Attribute tạm để None
    
    results = es_service.object_search(parsed_query)
    paginated_data, current_page, num_pages, total = paginate(results, params.page)
    
    return templates.TemplateResponse("home.html", {
        "request": request, "data": paginated_data, "page": current_page, "num_pages": num_pages,
        "search_type": "object", "result_count": total
    })

@app.get("/ic", response_class=HTMLResponse)
async def ic_api(request: Request, params: QueryParams = Depends()):
    """Tìm kiếm Image Captioning sử dụng ViT-L/14"""
    
    # Sử dụng model L14 (ID 6)
    service = faiss_services.get(6)
    
    if not service:
        logger.warning("Model L14 chưa được load!")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "data": [], 
            "error": "Model ViT-L/14 chưa được load! Hãy bật ID 6 trong config.",
            "page": 1,
            "num_pages": 1,
            "query": params.query,
            "search_type": "ic"
        })
    
    try:
        results = service.text_search(params.query, k=400)
        paginated_data, current_page, num_pages, total = paginate(results, params.page)
        
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "data": paginated_data, 
            "page": current_page, 
            "num_pages": num_pages,
            "query": params.query, 
            "search_type": "ic", 
            "result_count": total
        })
    except Exception as e:
        logger.error(f"Lỗi IC API: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "data": [], 
            "error": str(e),
            "page": 1, 
            "num_pages": 1
        })

# ==========================================
# 🎯 MULTI-CONTEXT KIS ENDPOINT
# ==========================================
class MultiContextRequest(BaseModel):
    context1: Optional[str] = ""
    context2: Optional[str] = ""
    context3: Optional[str] = ""
    faiss: int = 7  # Default model ID

@app.post("/api/multi-context-search")
async def multi_context_search_api(payload: MultiContextRequest):
    """
    API tìm kiếm multi-context
    Trả về JSON cho AJAX call
    """
    if not multi_context_kis:
        return JSONResponse(
            status_code=503,
            content={"error": "Multi-Context KIS chưa được khởi tạo"}
        )
    
    try:
        # Gộp contexts thành list
        contexts = [payload.context1, payload.context2, payload.context3]
        
        # Search
        results = multi_context_kis.search_multi_context(
            contexts=contexts,
            k=400,
            search_k=100
        )
        
        # Get video summary
        video_summary = multi_context_kis.get_video_summary(results)
        
        return JSONResponse(content={
            "success": True,
            "results": results[:100],  # Top 100 frames
            "video_summary": video_summary[:20],  # Top 20 videos
            "total_results": len(results)
        })
        
    except Exception as e:
        logger.error(f"Multi-Context Search Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/multi-context", response_class=HTMLResponse)
async def multi_context_ui(request: Request, params: QueryParams = Depends()):
    """
    Endpoint GET cho Multi-Context (để hiển thị UI hoặc handle query params)
    """
    if not multi_context_kis:
        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": [],
            "page": 1,
            "num_pages": 1,
            "error": "Multi-Context KIS chưa được khởi tạo"
        })
    
    # Lấy contexts từ query params
    context1 = request.query_params.get("context1", "")
    context2 = request.query_params.get("context2", "")
    context3 = request.query_params.get("context3", "")
    
    if not any([context1, context2, context3]):
        # Chưa có query, hiển thị trang trống
        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": [],
            "page": 1,
            "num_pages": 1,
            "search_type": "multi_context"
        })
    
    try:
        # Search
        contexts = [context1, context2, context3]
        results = multi_context_kis.search_multi_context(
            contexts=contexts,
            k=400,
            search_k=100
        )
        
        # Paginate
        paginated_data, current_page, num_pages, total = paginate(results, params.page)
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": paginated_data,
            "page": current_page,
            "num_pages": num_pages,
            "search_type": "multi_context",
            "result_count": total,
            "context1": context1,
            "context2": context2,
            "context3": context3
        })
        
    except Exception as e:
        logger.error(f"Multi-Context UI Error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "data": [],
            "error": str(e),
            "page": 1,
            "num_pages": 1,
            "search_type": "multi_context"
        })

# ==========================================
# 🚀 SUBMIT ENDPOINT
# ==========================================
class SubmitRequest(BaseModel):
    videoId: str
    frame: int
    fps: Optional[float] = 25.0
    timestampMs: Optional[int] = None  # Timestamp in milliseconds from video player

@app.post("/api/submit")
async def submit_frame(payload: SubmitRequest):
    """
    Submit frame to DRES competition server
    Returns HTTP 200 on success, HTTP 500 on error
    """
    try:
        # Use timestampMs if provided, otherwise calculate from frame
        if payload.timestampMs is not None:
            timestamp_to_use = payload.timestampMs
            logger.info(f"Using player timestamp: {timestamp_to_use}ms")
        else:
            # Calculate from frame index
            timestamp_to_use = int((payload.frame / payload.fps) * 1000)
            logger.info(f"Calculated from frame {payload.frame}: {timestamp_to_use}ms")
        
        result = {
            "videoId": payload.videoId,
            "timestamp": payload.frame,
            "timestampMs": timestamp_to_use
        }
        response = full_submission_flow(result, fps=payload.fps)
        
        # Extract detailed submission information from DRES response
        submission_info = {
            "success": True,
            "status": response.get("status"),  # CORRECT, WRONG, INDETERMINATE, etc.
            "description": response.get("description", ""),
            "submissionId": response.get("submissionId") or response.get("id"),
            "timestamp": timestamp_to_use,
            "videoId": payload.videoId,
            "frame": payload.frame,
            "evaluationId": response.get("evaluationId"),
            "raw_response": response  # Full DRES response for debugging
        }
        
        logger.info(f"Submission successful - Status: {submission_info['status']}, Description: {submission_info['description']}")
        
        # Return HTTP 200 OK with submission info
        return JSONResponse(status_code=200, content=submission_info)
        
    except Exception as e:
        logger.error(f"Submit error: {e}")
        
        # Return HTTP 500 Internal Server Error with error details
        error_info = {
            "success": False, 
            "status": "ERROR",
            "error": str(e),
            "description": f"Submission failed: {str(e)}",
            "videoId": payload.videoId,
            "frame": payload.frame,
            "timestamp": payload.timestampMs if payload.timestampMs else int((payload.frame / payload.fps) * 1000)
        }
        
        return JSONResponse(status_code=500, content=error_info)