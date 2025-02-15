"""
该模块提供翻译过程的日志记录功能。
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class TranslationLogger:
    def __init__(self, log_dir: str = "logs"):
        """
        初始化翻译日志记录器。
        
        参数：
            log_dir: 日志文件保存目录
        """
        self.log_dir = log_dir
        self._ensure_log_dir()
        self.current_log_file = self._create_log_file()
        self.segments: List[Dict] = []
        
    def _ensure_log_dir(self) -> None:
        """确保日志目录存在。"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def _create_log_file(self) -> str:
        """
        创建新的日志文件。
        
        返回：
            日志文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.log_dir, f"translation_log_{timestamp}.json")
    
    def log_segment(self, 
                   original_text: str, 
                   translated_text: str, 
                   segment_index: int,
                   total_segments: int,
                   metadata: Optional[Dict] = None,
                   rating_result: Optional[Dict] = None,
                   polished_text: Optional[str] = None) -> None:
        """
        记录一个翻译片段。
        
        参数：
            original_text: 原文内容
            translated_text: 翻译后的内容
            segment_index: 当前片段索引
            total_segments: 总片段数
            metadata: 额外的元数据信息
            rating_result: 翻译评分结果（仅在高质量模式下使用）
            polished_text: 润色后的文本（仅在需要润色时使用）
        """
        segment = {
            "segment_index": segment_index,
            "total_segments": total_segments,
            "original_text": original_text,
            "translated_text": translated_text,
            "timestamp": datetime.now().isoformat(),
        }
        
        if metadata:
            segment["metadata"] = metadata
            
        # 添加评分和润色信息（如果有）
        if rating_result:
            segment["rating"] = rating_result
            
        if polished_text:
            segment["polished_text"] = polished_text
            segment["final_text"] = polished_text
        else:
            segment["final_text"] = translated_text
            
        self.segments.append(segment)
        self._save_log()
        
    def _save_log(self) -> None:
        """将日志保存到文件。"""
        log_data = {
            "translation_segments": self.segments,
            "last_updated": datetime.now().isoformat(),
            "statistics": self._calculate_statistics()
        }
        
        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
    def _calculate_statistics(self) -> Dict:
        """
        计算翻译统计信息。
        
        返回：
            包含统计信息的字典
        """
        total_segments = len(self.segments)
        segments_with_rating = [s for s in self.segments if "rating" in s]
        segments_with_polish = [s for s in self.segments if "polished_text" in s]
        
        # 计算平均评分（如果有评分）
        avg_scores = {}
        if segments_with_rating:
            score_sums = {
                "accuracy": 0,
                "completeness": 0,
                "fluency": 0,
                "terminology": 0,
                "style": 0,
                "total_score": 0
            }
            
            for segment in segments_with_rating:
                rating = segment["rating"]
                for key in score_sums:
                    score_sums[key] += rating.get(key, 0)
            
            for key in score_sums:
                avg_scores[f"avg_{key}"] = round(score_sums[key] / len(segments_with_rating), 2)
        
        return {
            "total_segments": total_segments,
            "segments_with_rating": len(segments_with_rating),
            "segments_with_polish": len(segments_with_polish),
            "average_scores": avg_scores if segments_with_rating else None
        }
            
    def get_segment(self, segment_index: int) -> Optional[Dict]:
        """
        获取指定索引的翻译片段。
        
        参数：
            segment_index: 片段索引
            
        返回：
            翻译片段信息，如果不存在则返回None
        """
        for segment in self.segments:
            if segment["segment_index"] == segment_index:
                return segment
        return None
    
    def get_all_segments(self) -> List[Dict]:
        """
        获取所有翻译片段。
        
        返回：
            所有翻译片段的列表
        """
        return self.segments 

    def log_advanced_review(
        self,
        original_text: str,
        initial_translation: str,
        final_translation: str,
        review_result: str
    ) -> None:
        """
        记录高级模式下的审校结果。
        
        参数：
            original_text: 原文
            initial_translation: 初步译文
            final_translation: 最终润色后的译文
            review_result: 审校意见文本
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "advanced_review",
            "original_text": original_text,
            "initial_translation": initial_translation,
            "final_translation": final_translation,
            "review_comments": review_result
        }
        
        self.segments.append(log_entry)
        self._save_log() 