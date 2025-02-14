"""
该模块提供翻译过程的日志记录功能。
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

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
                   metadata: Optional[Dict] = None) -> None:
        """
        记录一个翻译片段。
        
        参数：
            original_text: 原文内容
            translated_text: 翻译后的内容
            segment_index: 当前片段索引
            total_segments: 总片段数
            metadata: 额外的元数据信息
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
            
        self.segments.append(segment)
        self._save_log()
        
    def _save_log(self) -> None:
        """将日志保存到文件。"""
        log_data = {
            "translation_segments": self.segments,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
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