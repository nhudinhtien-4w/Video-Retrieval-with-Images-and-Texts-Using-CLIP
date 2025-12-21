# import logging
# import json
# import os
# from elasticsearch import Elasticsearch

# # Setup logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# class EsService:
#     def __init__(self, host="http://localhost:9200", json_path=None):
#         """
#         Khởi tạo kết nối ES và load map ảnh.
#         """
#         # 1. Kết nối Elasticsearch
#         try:
#             self.es = Elasticsearch([host])
#             if not self.es.ping():
#                 logger.error(f"Không thể ping thấy ES tại {host}")
#             else:
#                 logger.info(f"Kết nối ES thành công tại {host}")
#         except Exception as e:
#             logger.error(f"Lỗi kết nối ES: {e}")
#             self.es = None

#         # 2. Load Mapping JSON (Để map ID -> Image Path)
#         self.id_map = {}
#         if json_path and os.path.exists(json_path):
#             logger.info(f"Loading Map for ES: {json_path}")
#             with open(json_path, 'r') as f:
#                 self.id_map = {int(k): v for k, v in json.load(f).items()}
#         else:
#             logger.warning("Không tìm thấy file JSON map cho ES.")

#     def _format_results(self, ids, scores=None):
#         """Hàm phụ trợ: Map từ ID sang format chuẩn {id, path, score}"""
#         results = []
#         # Nếu không có score (như Object Search), mặc định là 1.0
#         if scores is None:
#             scores = [1.0] * len(ids)
            
#         for idx, score in zip(ids, scores):
#             try:
#                 idx = int(idx) # Đảm bảo ID là int
#                 if idx in self.id_map:
#                     results.append({
#                         "id": idx,
#                         "score": score,
#                         "imgpath": self.id_map[idx]
#                     })
#             except ValueError:
#                 continue # Bỏ qua nếu ID lỗi
#         return results

#     def ocr_search(self, query, index_name="ocr", size=100):
#         if not self.es: return []
        
#         try:
#             # 1. Exact Match (Ưu tiên cao)
#             exact_body = {
#                 "query": {"match": {"ocr": {"query": query, "operator": "and"}}},
#                 "size": size
#             }
#             res_exact = self.es.search(index=index_name, body=exact_body)['hits']['hits']
            
#             # 2. Fuzzy Match (Tìm mờ)
#             fuzzy_body = {
#                 "query": {"multi_match": {"query": query, "fields": ["ocr"], "fuzziness": "AUTO"}},
#                 "size": size
#             }
#             res_fuzzy = self.es.search(index=index_name, body=fuzzy_body)['hits']['hits']
            
#             # 3. Gộp kết quả (Ưu tiên Exact trước)
#             seen_ids = set()
#             final_ids = []
#             final_scores = []
            
#             # Hàm phụ để add hits
#             def add_hits(hits):
#                 for hit in hits:
#                     _id = hit['_id']
#                     if _id not in seen_ids:
#                         seen_ids.add(_id)
#                         final_ids.append(_id)
#                         final_scores.append(hit['_score'])

#             add_hits(res_exact)
#             add_hits(res_fuzzy)
            
#             return self._format_results(final_ids, final_scores)
            
#         except Exception as e:
#             logger.error(f"Lỗi OCR Search: {e}")
#             return []

#     def asr_search(self, query, index_name="asr", size=100):
#         if not self.es: return []
        
#         try:
#             body = {
#                 "query": {"multi_match": {"query": query, "fields": ["asr"], "fuzziness": "AUTO"}},
#                 "size": size
#             }
#             hits = self.es.search(index=index_name, body=body)['hits']['hits']
            
#             ids = [hit['_id'] for hit in hits]
#             scores = [hit['_score'] for hit in hits]
            
#             return self._format_results(ids, scores)
#         except Exception as e:
#             logger.error(f"Lỗi ASR Search: {e}")
#             return []

#     def object_search(self, query_list, index_name="objects", size=200):
#         """
#         query_list: List các tuple [(quantity, name, attribute), ...]
#         """
#         if not self.es: return []
        
#         try:
#             must_clauses = []
#             for item in query_list:
#                 # Logic parse query object (giữ nguyên logic cũ của bạn)
#                 try:
#                     quantity, name, attribute = item
#                     clause = {
#                         "nested": {
#                             "path": "objects",
#                             "query": {
#                                 "bool": {
#                                     "must": []
#                                 }
#                             }
#                         }
#                     }
#                     nested_must = clause["nested"]["query"]["bool"]["must"]
                    
#                     if name != "None": nested_must.append({"match": {"objects.name": name}})
#                     if attribute != "None": nested_must.append({"match": {"objects.attribute": attribute}})
                    
#                     if quantity != "None":
#                         nested_must.append({"range": {"objects.quantity": {"gte": int(quantity)}}})
                    
#                     must_clauses.append(clause)
#                 except Exception as e:
#                     logger.warning(f"Lỗi parse object query item {item}: {e}")
#                     continue

#             if not must_clauses: return []

#             body = {
#                 "query": {"bool": {"must": must_clauses}},
#                 "_source": False, # Chỉ lấy ID cho nhẹ
#                 "size": size
#             }
            
#             hits = self.es.search(index=index_name, body=body)['hits']['hits']
#             ids = [hit['_id'] for hit in hits]
            
#             # Object search thường không quan trọng score, trả về theo thứ tự tìm thấy
#             return self._format_results(ids)
            
#         except Exception as e:
#             logger.error(f"Lỗi Object Search: {e}")
#             return []


import logging
import json
import os
from elasticsearch import Elasticsearch

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EsService:
    def __init__(self, host="http://localhost:9200", json_path=None):
        """
        Khởi tạo kết nối ES và load map ảnh.
        """
        # 1. Kết nối Elasticsearch
        try:
            # Sửa lại cho đúng cú pháp thư viện mới
            self.es = Elasticsearch(host)
            if not self.es.ping():
                logger.error(f"Không thể ping thấy ES tại {host}")
                self.es = None
            else:
                logger.info(f"Kết nối ES thành công tại {host}")
                if index_data(self.es, 'data/es_data'):
                    logger.info("Đã index dữ liệu thành công")
                else:
                    logger.error("Không thể index dữ liệu")
        except Exception as e:
            logger.error(f"Lỗi kết nối ES: {e}")
            self.es = None

        # 2. Load Mapping JSON (Để map ID -> Image Path)
        self.id_map = {}
        if json_path and os.path.exists(json_path):
            logger.info(f"Loading Map for ES: {json_path}")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    # Chuyển key thành int để map cho chính xác
                    self.id_map = {int(k): v for k, v in json.load(f).items()}
            except Exception as e:
                logger.error(f"Lỗi đọc file map: {e}")
        else:
            logger.warning("Không tìm thấy file JSON map, kết quả trả về sẽ không có đường dẫn ảnh.")

    def _format_results(self, ids, scores=None):
        """Map từ ID sang format {id, imgpath, score}"""
        results = []
        if scores is None:
            scores = [1.0] * len(ids)
            
        for idx, score in zip(ids, scores):
            try:
                # Xử lý trường hợp ID trả về dạng string
                idx_int = int(idx) 
                path = self.id_map.get(idx_int, "")
                
                results.append({
                    "id": idx_int,
                    "score": score,
                    "imgpath": f"/{path}" if path else ""
                })
            except ValueError:
                continue 
        return results

    def object_search(self, query_list, index_name="object", size=200):
        """
        query_list: List các tuple [(quantity, name, attribute), ...]
        Logic: Nested Query
        """
        if not self.es: return []
        
        try:
            must_clauses = []
            for item in query_list:
                try:
                    quantity, name, attribute = item
                    # Xây dựng Nested Query
                    nested_bool = {"must": []}
                    
                    if name and name != "None": 
                        nested_bool["must"].append({"match": {"objects.name": name}})
                    if attribute and attribute != "None": 
                        nested_bool["must"].append({"match": {"objects.attribute": attribute}})
                    if quantity and quantity != "None":
                         nested_bool["must"].append({"range": {"objects.quantity": {"gte": int(quantity)}}})
                    
                    # Chỉ thêm vào clause nếu có ít nhất 1 điều kiện
                    if nested_bool["must"]:
                        clause = {
                            "nested": {
                                "path": "objects",
                                "query": {"bool": nested_bool}
                            }
                        }
                        must_clauses.append(clause)
                        
                except Exception as e:
                    logger.warning(f"Lỗi parse object item {item}: {e}")
                    continue

            if not must_clauses: return []

            body = {
                "query": {"bool": {"must": must_clauses}},
                "_source": False, # Chỉ cần ID
                "size": size
            }
            
            hits = self.es.search(index=index_name, body=body)['hits']['hits']
            ids = [hit['_id'] for hit in hits]
            
            return self._format_results(ids) # Object search thường không care score
            
        except Exception as e:
            logger.error(f"Lỗi Object Search: {e}")
            return []