"""
Multi-Context KIS (Known-Item Search)
Tìm kiếm video chứa nhiều ngữ cảnh (contexts) khác nhau

Use Case:
- Context 1: "Một người đàn ông đeo kính"
- Context 2: "Một chiếc xe màu đỏ"  
- Context 3: "Một tòa nhà cao tầng"
=> Tìm video chứa CẢ 3 contexts này (ở các frame khác nhau)
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class MultiContextKIS:
    """
    Multi-Context Video Search
    Tìm video chứa nhiều ngữ cảnh/sự kiện khác nhau
    """
    
    def __init__(self, faiss_service, es_service=None):
        self.faiss = faiss_service
        self.es = es_service
        
    def search_single_context(self, context: str, k: int = 100) -> List[Dict]:
        """
        Tìm kiếm cho 1 context
        """
        if not context or not context.strip():
            return []
        
        try:
            results = self.faiss.text_search(context.strip(), k=k)
            logger.info(f"Context '{context[:50]}...' found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search error for context: {e}")
            return []
    
    def extract_video_id(self, imgpath: str) -> Optional[str]:
        """
        Extract video ID từ image path
        Format: L01_V001/frame_123.jpg -> L01_V001
        """
        try:
            parts = imgpath.split('/')
            if len(parts) >= 1:
                return parts[0]  # L01_V001
            return None
        except:
            return None
    
    def multi_context_fusion(
        self, 
        context_results: List[List[Dict]], 
        k: int = 100,
        min_contexts: int = 2
    ) -> List[Dict]:
        """
        Kết hợp kết quả từ nhiều contexts
        
        Strategy: Tìm video xuất hiện trong NHIỀU contexts nhất
        
        Args:
            context_results: List of results từ mỗi context [[ctx1_results], [ctx2_results], ...]
            k: Số kết quả trả về
            min_contexts: Video phải xuất hiện trong ít nhất bao nhiêu contexts
        
        Returns:
            List of videos ranked by số contexts matched và score
        """
        # Dictionary: video_id -> {contexts, frames, scores}
        video_data = defaultdict(lambda: {
            'contexts': set(),  # Các context nào video này xuất hiện
            'frames': [],       # Tất cả frames
            'scores': [],       # Tất cả scores
            'context_frames': defaultdict(list)  # frames cho mỗi context
        })
        
        # Thu thập data từ mỗi context
        for context_idx, results in enumerate(context_results):
            if not results:
                continue
                
            for item in results:
                video_id = self.extract_video_id(item['imgpath'])
                if not video_id:
                    continue
                
                video_data[video_id]['contexts'].add(context_idx)
                video_data[video_id]['frames'].append(item)
                video_data[video_id]['scores'].append(item.get('score', 0))
                video_data[video_id]['context_frames'][context_idx].append(item)
        
        # Lọc videos có đủ min_contexts
        qualified_videos = {
            vid: data for vid, data in video_data.items()
            if len(data['contexts']) >= min_contexts
        }
        
        if not qualified_videos:
            logger.warning(f"No videos found with {min_contexts}+ contexts. Lowering threshold...")
            # Nếu không có video nào match đủ, giảm threshold
            qualified_videos = {
                vid: data for vid, data in video_data.items()
                if len(data['contexts']) >= 1
            }
        
        # Tính ranking score cho mỗi video
        ranked_videos = []
        for video_id, data in qualified_videos.items():
            num_contexts = len(data['contexts'])
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            max_score = max(data['scores']) if data['scores'] else 0
            num_frames = len(data['frames'])
            
            # Ranking formula: 
            # - Ưu tiên video có nhiều contexts
            # - Sau đó ưu tiên score cao
            # - Cuối cùng ưu tiên nhiều frames (evidence)
            ranking_score = (
                num_contexts * 1000 +  # Contexts là quan trọng nhất
                avg_score * 100 +      # Avg score
                num_frames * 1        # Số lượng frames (evidence)
            )
            
            # Lấy best frame từ mỗi context
            context_best_frames = {}
            for ctx_idx, frames in data['context_frames'].items():
                best_frame = max(frames, key=lambda x: x.get('score', 0))
                context_best_frames[ctx_idx] = best_frame
            
            ranked_videos.append({
                'video_id': video_id,
                'ranking_score': ranking_score,
                'num_contexts_matched': num_contexts,
                'total_contexts': len(context_results),
                'coverage': num_contexts / len(context_results),
                'avg_score': avg_score,
                'max_score': max_score,
                'num_frames': num_frames,
                'all_frames': sorted(data['frames'], key=lambda x: x.get('score', 0), reverse=True),
                'context_best_frames': context_best_frames,
                'matched_contexts': list(data['contexts'])
            })
        
        # Sort by ranking_score
        ranked_videos.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        logger.info(f"Multi-context fusion: {len(ranked_videos)} videos qualified")
        
        # Flatten về format cũ (list of frames) nhưng ưu tiên video tốt
        final_results = []
        for video_info in ranked_videos[:k]:
            # Thêm metadata vào từng frame
            for frame in video_info['all_frames'][:10]:  # Top 10 frames/video
                final_results.append({
                    **frame,
                    'video_id': video_info['video_id'],
                    'multi_context_score': video_info['ranking_score'],
                    'contexts_matched': video_info['num_contexts_matched'],
                    'coverage': video_info['coverage'],
                    'is_multi_context': True
                })
        
        return final_results
    
    def search_multi_context(
        self, 
        contexts: List[str], 
        k: int = 100,
        search_k: int = 100,
        min_contexts: Optional[int] = None
    ) -> List[Dict]:
        """
        Main API: Tìm kiếm với nhiều contexts
        
        Args:
            contexts: List of context strings (có thể empty)
            k: Số kết quả cuối cùng
            search_k: Số kết quả cho mỗi context search
            min_contexts: Tối thiểu bao nhiêu contexts phải match (default: len(contexts))
        
        Returns:
            Ranked list of frames từ videos tốt nhất
        """
        # Loại bỏ contexts rỗng
        valid_contexts = [c.strip() for c in contexts if c and c.strip()]
        
        if not valid_contexts:
            logger.warning("No valid contexts provided")
            return []
        
        logger.info(f"Multi-context search with {len(valid_contexts)} contexts")
        
        # Search từng context
        all_results = []
        for idx, context in enumerate(valid_contexts):
            logger.info(f"Searching context {idx+1}/{len(valid_contexts)}: {context[:50]}...")
            results = self.search_single_context(context, k=search_k)
            all_results.append(results)
        
        # Nếu chỉ có 1 context, return luôn
        if len(valid_contexts) == 1:
            return all_results[0][:k]
        
        # Fusion nhiều contexts
        if min_contexts is None:
            # Default: Yêu cầu match ít nhất 2 contexts (hoặc tất cả nếu có 2)
            min_contexts = min(2, len(valid_contexts))
        
        fused_results = self.multi_context_fusion(
            all_results, 
            k=k,
            min_contexts=min_contexts
        )
        
        return fused_results
    
    def get_video_summary(self, results: List[Dict]) -> List[Dict]:
        """
        Tạo summary theo video (để hiển thị)
        
        Returns:
            [
                {
                    'video_id': 'L01_V001',
                    'contexts_matched': 3,
                    'total_frames': 15,
                    'best_frame': {...},
                    'sample_frames': [...]
                }
            ]
        """
        video_summary = defaultdict(lambda: {
            'frames': [],
            'contexts': set(),
            'scores': []
        })
        
        for item in results:
            video_id = item.get('video_id') or self.extract_video_id(item['imgpath'])
            if not video_id:
                continue
            
            video_summary[video_id]['frames'].append(item)
            video_summary[video_id]['scores'].append(item.get('score', 0))
            if 'contexts_matched' in item:
                video_summary[video_id]['contexts'].add(item['contexts_matched'])
        
        summaries = []
        for video_id, data in video_summary.items():
            best_frame = max(data['frames'], key=lambda x: x.get('score', 0))
            summaries.append({
                'video_id': video_id,
                'contexts_matched': data['frames'][0].get('contexts_matched', 0),
                'total_frames': len(data['frames']),
                'avg_score': sum(data['scores']) / len(data['scores']) if data['scores'] else 0,
                'best_frame': best_frame,
                'sample_frames': data['frames'][:5]  # Top 5 frames
            })
        
        summaries.sort(key=lambda x: x['contexts_matched'], reverse=True)
        return summaries
