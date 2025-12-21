import os
import json
import faiss
import torch
import numpy as np
import logging
from PIL import Image

import open_clip
import clip # OpenAI CLIP
from sentence_transformers import SentenceTransformer
from langdetect import detect
    
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaissService:
    def __init__(self, bin_path, json_path, model_type="open_clip", model_name="ViT-B-32", device="cpu", translator=None, pretrained=None):
        """
        Args:
            model_type: "open_clip", "openai", "sentence_transformer"
            model_name: Tên model cụ thể (vd: "ViT-B/32")
            pretrained: Pretrained weights cho open_clip (vd: "openai", "laion2b_s34b_b79k")
        """
        self.device = device
        self.translator = translator
        self.model_type = model_type
        self.model_name = model_name
        self.pretrained = pretrained
        
        # 1.LOAD INDEX FAISS 
        if not os.path.exists(bin_path):
            raise FileNotFoundError(f"Index not found: {bin_path}")
        
        logger.info(f"Loading Index: {bin_path}")
        self.index = faiss.read_index(bin_path)
        # chuyển index sang GPU nếu có
        if device == "cuda":
            try: 
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("Đã chuyển FAISS index sang GPU")
            except Exception as e:
                logger.warning(f"Không thể chuyển index sang GPU: {e}, dùng CPU.")

        # 2. LOAD MAPPING JSON 
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON Map not found: {json_path}")
            
        logger.info(f"Loading Map: {json_path}")
        with open(json_path, 'r') as f:
            # Map ID (int) -> Path (str)
            self.id_map = {int(k): v for k, v in json.load(f).items()}

        # 3. LOAD AI MODEL
        logger.info(f"Loading Model: {model_type} - {model_name}")
        
        if model_type == "open_clip":
            # Xử lý cho OpenCLIP (Gồm cả QuickGELU)
            # Ưu tiên dùng pretrained từ config, nếu không có thì auto-detect
            if pretrained is None:
                pretrained = 'dfn5b' if 'quickgelu' in model_name else 'laion2b_s34b_b79k'
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
            self.model.to(device).eval()
            self.tokenizer = open_clip.get_tokenizer(model_name)
            
        elif model_type == "openai":
            # Xử lý cho OpenAI CLIP gốc
            self.model, self.preprocess = clip.load(model_name, device=device)
            
        elif model_type == "sentence_transformer":
            # Xử lý cho Sentence Transformers
            self.model = SentenceTransformer(model_name, device=device)

    def _normalize(self, x):
        return x / np.linalg.norm(x, axis=1, keepdims=True)

    def text_search(self, text: str, k: int = 100):
        # 1. Dịch thuật (Nếu có translator truyền vào)
        if self.translator:
            if detect(text) == 'vi':
                text = self.translator(text) 
        # 2. Encode Text thành Vector (Tùy loại model)
        vector = None
        with torch.no_grad():
            if self.model_type == "open_clip":
                tokens = self.tokenizer([text]).to(self.device)
                feat = self.model.encode_text(tokens)
                vector = feat.cpu().numpy()
                
            elif self.model_type == "openai":
                tokens = clip.tokenize([text]).to(self.device)
                feat = self.model.encode_text(tokens)
                vector = feat.cpu().numpy()
                
            elif self.model_type == "sentence_transformer":
                vector = self.model.encode([text]) # SentenceTransformer tự ra numpy

        # 3. Chuẩn hóa & Search FAISS
        if vector is not None:
            vector = vector.astype(np.float32)
            vector = self._normalize(vector)
            
            scores, ids = self.index.search(vector, k)
            
            # 4. Map kết quả trả về List Dict đẹp
            results = []
            for score, idx in zip(scores[0], ids[0]):
                idx = int(idx)
                if idx in self.id_map:
                    results.append({
                        "id": idx,
                        "score": float(score),
                        "imgpath": f"/{self.id_map[idx]}"
                    })
            return results
        return []

    # Hàm search bằng ảnh (Dùng chung cho cả 2 loại CLIP)
    def image_search(self, img_id: int, k: int = 100):
        # Reconstruct vector từ Index (Không cần model AI chạy lại)
        try:
            vector = self.index.reconstruct(img_id).reshape(1, -1).astype(np.float32)
            scores, ids = self.index.search(vector, k)
            
            results = []
            for score, idx in zip(scores[0], ids[0]):
                idx = int(idx)
                if idx in self.id_map:
                    results.append({
                        "id": idx,
                        "score": float(score),
                        "imgpath": f"/{self.id_map[idx]}"
                    })
            return results
        except Exception as e:
            logger.error(f"Error image search id {img_id}: {e}")
            return []