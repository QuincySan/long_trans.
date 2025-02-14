"""
该模块负责将Markdown文本分割成更小的段落。
支持两级分段策略：
1. 大段（约20,000字）用于生成摘要
2. 小段（约5,000字）用于实际翻译
"""
from typing import List
import re

class Chunker:
    def __init__(self, large_chunk_size: int = 20000, small_chunk_size: int = 5000):
        """
        使用最大块大小初始化分段器。
        
        参数：
            large_chunk_size: 大块的最大字符数（用于摘要）
            small_chunk_size: 小块的最大字符数（用于翻译）
        """
        self.large_chunk_size = large_chunk_size
        self.small_chunk_size = small_chunk_size

    def split_for_summary(self, text: str) -> List[str]:
        """
        将输入文本分割成大块（约20,000字），用于生成摘要。
        """
        return self._split_text(text, self.large_chunk_size)

    def split_for_translation(self, text: str) -> List[str]:
        """
        将输入文本分割成小块（约5,000字），用于翻译。
        """
        return self._split_text(text, self.small_chunk_size)

    def _split_text(self, text: str, max_size: int) -> List[str]:
        """
        将输入文本分割成块，同时保持Markdown结构。
        优化后的分块策略：
        1. 文本较短时直接返回
        2. 保持标题与其内容在同一块
        3. 智能合并多个section_block直到接近max_size
        """
        # 1. 如果文本较短，直接返回
        if len(text) < max_size * 0.8:  # 给一个0.8的buffer
            return [text]

        # 2. 按标题分割，保持"标题+内容"作为最小单元
        raw_sections = re.split(r'(#{1,6}\s[^\n]+\n)', text)
        section_blocks = []
        i = 0
        
        while i < len(raw_sections):
            # 处理开头非标题的情况
            if i == 0 and not re.match(r'^#{1,6}\s', raw_sections[i]):
                if raw_sections[i].strip():
                    section_blocks.append(raw_sections[i])
                i += 1
                continue

            # 处理标题及其内容
            if re.match(r'^#{1,6}\s', raw_sections[i]):
                block_content = raw_sections[i]
                if i + 1 < len(raw_sections) and not re.match(r'^#{1,6}\s', raw_sections[i+1]):
                    block_content += raw_sections[i+1]
                    i += 1
                section_blocks.append(block_content)
            else:
                section_blocks.append(raw_sections[i])
            i += 1

        # 3. 智能合并section_blocks
        chunks = []
        current_chunk = ""

        for block in section_blocks:
            if len(current_chunk) + len(block) <= max_size:
                current_chunk += block
            else:
                if not current_chunk:
                    # 单个block超长，需要进一步分割
                    sub_blocks = self._further_split_block(block, max_size)
                    chunks.extend(sub_blocks)
                else:
                    chunks.append(current_chunk)
                    current_chunk = block

        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks

    def _further_split_block(self, block: str, max_size: int) -> List[str]:
        """
        对超长块进行更细粒度的分割，优先按段落分，必要时按句子分。
        """
        paragraphs = re.split(r'\n\s*\n', block)
        result = []
        temp_chunk = ""

        for p in paragraphs:
            if len(p) > max_size:
                if temp_chunk:
                    result.append(temp_chunk)
                    temp_chunk = ""
                result.extend(self._split_by_sentence(p, max_size))
            else:
                if len(temp_chunk) + len(p) + 2 > max_size:
                    result.append(temp_chunk)
                    temp_chunk = p
                else:
                    if temp_chunk:
                        temp_chunk += "\n\n"
                    temp_chunk += p

        if temp_chunk:
            result.append(temp_chunk)
        return result

    def _split_by_sentence(self, text: str, max_size: int) -> List[str]:
        """
        按句子边界进行最细粒度的分割。
        支持中英文标点符号。
        """
        # 同时处理中英文标点
        sentences = re.split(r'([。！？.!?])', text)
        chunks = []
        current_chunk = ""

        # 将标点符号与前面的句子重新组合
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i+1]
            else:
                sentence = sentences[i]

            if len(current_chunk) + len(sentence) > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence

        if current_chunk:
            chunks.append(current_chunk)
        return chunks 