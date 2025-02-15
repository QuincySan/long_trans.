"""
该模块负责将Markdown文本分割成更小的段落。
支持两级分段策略：
1. 大段（约20,000词）用于生成摘要
2. 小段（约2,000词）用于实际翻译
"""
from typing import List
import re

class Chunker:
    def __init__(self, large_chunk_size: int = 20000, small_chunk_size: int = 2000):
        """
        使用最大块大小初始化分段器。
        
        参数：
            large_chunk_size: 大块的最大单词数（用于摘要）
            small_chunk_size: 小块的最大单词数（用于翻译）
        """
        self.large_chunk_size = large_chunk_size
        self.small_chunk_size = small_chunk_size

    def _count_words(self, text: str) -> int:
        """
        计算文本中的单词数。
        同时支持英文单词和中文字。
        默认包含代码块在内，不再移除 ```...```。
        
        参数：
            text: 输入文本
        返回：
            单词数量
        """
        # 直接把所有文字都当作可统计对象
        # 1. 匹配英文单词（含数字、连字符）
        english_words = len(re.findall(r'\b\w+(?:[-\']\w+)*\b', text))

        # 2. 匹配中文字（每个汉字算一个词）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

        return english_words + chinese_chars

    def split_for_summary(self, text: str) -> List[str]:
        """
        将输入文本分割成大块（约20,000词），用于生成摘要。
        """
        return self._split_text(text, self.large_chunk_size)

    def split_for_translation(self, text: str) -> List[str]:
        """
        将输入文本分割成小块（约2,000词），用于翻译。
        """
        return self._split_text(text, self.small_chunk_size)

    def _split_text(self, text: str, max_size: int) -> List[str]:
        """
        将输入文本分割成块，同时保持Markdown结构（优先在标题处分割）。
        优化策略：
        1. 若文本整体小于 max_size * 0.8 则不拆分
        2. 先按标题分割为最小单元
        3. 合并多个section直到接近max_size
        4. 如果某个section本身超过max_size，进入更细粒度拆分
        """
        # 1. 如果文本较短，直接返回
        if self._count_words(text) < max_size * 0.8:
            return [text]

        # 2. 按标题分割：先拆出标题行 + 其后内容
        # 用以下正则把标题行与非标题行分开
        raw_sections = re.split(r'(#{1,6}\s[^\n]+\n)', text)

        # 收集处理过的 section 块
        section_blocks = []
        i = 0
        while i < len(raw_sections):
            # 处理文本开头，如果不是标题，就直接收进一个块
            if i == 0 and not re.match(r'^#{1,6}\s', raw_sections[i]):
                if raw_sections[i].strip():
                    section_blocks.append(raw_sections[i])
                i += 1
                continue

            # 如果是标题，则和它后面的内容合并
            if re.match(r'^#{1,6}\s', raw_sections[i]):
                block_content = raw_sections[i]
                if i + 1 < len(raw_sections) and not re.match(r'^#{1,6}\s', raw_sections[i+1]):
                    block_content += raw_sections[i+1]
                    i += 1
                section_blocks.append(block_content)
            else:
                # 剩余情况，直接加入
                section_blocks.append(raw_sections[i])
            i += 1

        # 3. 合并section_blocks，直到累积的词数逼近 max_size
        chunks = []
        current_chunk = ""
        current_word_count = 0

        for block in section_blocks:
            block_word_count = self._count_words(block)
            if current_word_count + block_word_count <= max_size:
                # 继续往当前块里塞
                current_chunk += block
                current_word_count += block_word_count
            else:
                # 如果当前块为空，说明 block 本身就超标
                if not current_chunk:
                    # 进入更细粒度拆分（段落/句子）
                    sub_blocks = self._further_split_block(block, max_size)
                    chunks.extend(sub_blocks)
                else:
                    # 把已有的块先收起来，再把block作为新块开始
                    chunks.append(current_chunk)
                    current_chunk = block
                    current_word_count = block_word_count

        # 收尾
        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks

    def _further_split_block(self, block: str, max_size: int) -> List[str]:
        """
        对超长块进行更细粒度的分割，优先按段落分。
        在段落中如果依然超标，则再按句子分。
        """
        # 先检查是否包含代码块，如果有则优先保持代码块完整
        code_blocks = re.finditer(r'(```[^`]*```)', block)
        code_block_spans = [(m.start(), m.end()) for m in code_blocks]
        
        if code_block_spans:
            # 如果有代码块，按代码块分割文本
            result = []
            last_end = 0
            
            for start, end in code_block_spans:
                # 处理代码块前的文本
                if start > last_end:
                    pre_text = block[last_end:start]
                    if pre_text.strip():
                        result.extend(self._split_paragraphs(pre_text, max_size))
                
                # 保持代码块完整
                code_block = block[start:end]
                result.append(code_block)
                last_end = end
            
            # 处理最后一个代码块后的文本
            if last_end < len(block):
                post_text = block[last_end:]
                if post_text.strip():
                    result.extend(self._split_paragraphs(post_text, max_size))
            
            return result
        else:
            # 如果没有代码块，按常规方式分割
            return self._split_paragraphs(block, max_size)

    def _split_paragraphs(self, text: str, max_size: int) -> List[str]:
        """
        按段落分割文本，如果段落过大则按句子分割。
        """
        paragraphs = re.split(r'\n\s*\n', text)
        result = []
        temp_chunk = ""
        current_word_count = 0

        for p in paragraphs:
            p_word_count = self._count_words(p)
            if p_word_count > max_size:
                # 若temp_chunk不空，先把之前的内容收集起来
                if temp_chunk:
                    result.append(temp_chunk)
                    temp_chunk = ""
                    current_word_count = 0
                # 继续对这个超大的段落按句子切分
                result.extend(self._split_by_sentence(p, max_size))
            else:
                # 如果加上这个段落就超出max_size，则把temp_chunk收集到result
                if current_word_count + p_word_count > max_size:
                    result.append(temp_chunk)
                    temp_chunk = p
                    current_word_count = p_word_count
                else:
                    # 继续往temp_chunk拼接
                    if temp_chunk:
                        temp_chunk += "\n\n"
                    temp_chunk += p
                    current_word_count += p_word_count

        # 最后收尾
        if temp_chunk:
            result.append(temp_chunk)
        return result

    def _split_by_sentence(self, text: str, max_size: int) -> List[str]:
        """
        按句子边界进行最细粒度的分割。
        包含中英文标点。
        """
        # 同时处理中英文标点
        sentences = re.split(r'([。！？.!?])', text)
        chunks = []
        current_chunk = ""
        current_word_count = 0

        # 将标点符号与前一句合并
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i+1]
            else:
                sentence = sentences[i]

            sentence_word_count = self._count_words(sentence)
            if current_word_count + sentence_word_count > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                current_word_count = sentence_word_count
            else:
                current_chunk += sentence
                current_word_count += sentence_word_count

        if current_chunk:
            chunks.append(current_chunk)
        return chunks 