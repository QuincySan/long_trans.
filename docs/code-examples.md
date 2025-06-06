### 五、示例流程代码片段

#### **summarizer.py（简化示例）**

```python
"""
该模块负责生成文本摘要。
"""
from typing import Optional
from llm_client import ZetaClient

class Summarizer:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化摘要生成器。
        
        参数：
            api_key: LLM服务的API密钥
            api_base: LLM服务的API基础URL
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)

    def summarize(self, text: str) -> str:
        """
        对输入文本生成摘要。
        
        参数：
            text: 要生成摘要的Markdown文本
            
        返回：
            生成的摘要文本
        """
        prompt = (
            "请对以下文本生成一个简要的摘要。"
            "摘要应不超过500字，并使用中文输出：\n\n"
            f"{text}"
        )
        
        # 使用非流式输出，直接获取完整摘要
        summary = self.llm_client.generate_text(
            prompt=prompt,
            stream=False,
            model="claude-3-5-sonnet-20241022"
        )
        return summary.strip()
```

#### **translator.py（简化示例）**

```python
"""
该模块负责使用大语言模型(LLM)进行文本翻译。
支持基础和高级两种翻译等级。
"""
from typing import List, Optional, Dict, Any, Tuple
from llm_client import ZetaClient
from utils.translation_logger import TranslationLogger

class Translator:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, 
                 default_model: str = "deepseek-v3", quality_level: str = "basic"):
        """
        使用API凭证初始化翻译器。
        
        参数：
            api_key: 可选的API密钥。如果未提供，将尝试从环境变量获取。
            api_base: 可选的API基础URL。如果未提供，将尝试从环境变量获取。
            default_model: 默认使用的模型名称。
            quality_level: 翻译质量等级，可选值：basic（基础）, advanced（高级）
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)
        self.logger = TranslationLogger()
        self.default_model = default_model
        self.quality_level = quality_level

    def _build_translation_prompts(self, text: str, summary: Optional[str] = None) -> Tuple[str, str]:
        """
        构建翻译的system prompt和user prompt。
        
        参数：
            text: 要翻译的文本
            summary: 可选的上下文摘要
            
        返回：
            (system_prompt, user_prompt) 元组
        """
        system_prompt = (
            """你是一个专业的翻译助手。你的任务是将文本翻译成简体中文，同时：
1. 保持原有的Markdown格式和结构
2. 注意标题和正文之间的换行
3. 仅翻译文字内容，保留代码块、链接URL等不需要翻译的部分
4. 根据上下文准确理解专业术语，在后面加括号展示专业术语英文原文
5. 直接给出翻译内容，不要输出任何解释说明"""
        )
        
        if summary:
            user_prompt = (
                f"""【背景摘要】:
{summary}

【待翻译文本】:
{text}"""
            )
        else:
            user_prompt = text
        
        return system_prompt, user_prompt

    def translate_text(
        self,
        text: str,
        stream: bool = True,
        model: Optional[str] = None,
        summary: Optional[str] = None
    ) -> str:
        """
        翻译给定的文本，同时保持Markdown格式。
        
        参数：
            text: 要翻译的文本（Markdown格式）
            stream: 是否使用流式模式
            model: 使用的模型名称，如果未提供则使用默认模型
            summary: 可选的上下文摘要
            
        返回：
            保持Markdown格式的翻译后文本
        """
        model = model or self.default_model
        system_prompt, user_prompt = self._build_translation_prompts(text, summary)
        response_format = self._get_response_format(model)

        if stream:
            response_iterator = self.llm_client.generate_text(
                prompt=user_prompt,
                stream=True,
                model=model,
                system_prompt=system_prompt,
                response_format=response_format
            )
            translated_text = self._process_stream_response(response_iterator)
        else:
            translated_text = self.llm_client.generate_text(
                prompt=user_prompt,
                stream=False,
                model=model,
                system_prompt=system_prompt,
                response_format=response_format
            )

        return translated_text

    def translate_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        summary: Optional[str] = None
    ) -> List[str]:
        """
        批量翻译文本段落。使用 self.translate_text。
        
        参数：
            texts: 要翻译的文本段落列表
            model: 使用的模型名称，如果未提供则使用默认模型
            summary: 可选的上下文摘要
            
        返回：
            翻译后的文本段落列表
        """
        model = model or self.default_model
        total = len(texts)
        results = []
        
        for i, text in enumerate(texts, 1):
            result = self.translate_text(text, model=model, summary=summary)
            
            # 记录翻译结果
            metadata = {
                "model": model,
                "stream": True,
                "summary": summary,
                "quality_level": self.quality_level
            }
            
            self.logger.log_segment(
                original_text=text,
                translated_text=result,
                segment_index=i,
                total_segments=total,
                metadata=metadata
            )
            
            results.append(result)
            
        return results
```

#### **chunker.py（简化示例）**

```python
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
        
        参数：
            text: 输入文本
            
        返回：
            单词数量
        """
        # 移除代码块，避免代码中的标识符被计入
        text = re.sub(r'```[^`]*```', '', text)
        
        # 分别计算英文单词和中文字
        # 1. 匹配英文单词（包括带连字符和数字的单词）
        english_words = len(re.findall(r'\b\w+(?:[-\']\w+)*\b', text))
        
        # 2. 匹配中文字（每个中文字算作一个词）
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
        将输入文本分割成块，同时保持Markdown结构。
        优化后的分块策略：
        1. 文本较短时直接返回
        2. 保持标题与其内容在同一块
        3. 智能合并多个section_block直到接近max_size
        """
        # 如果文本较短，直接返回
        if self._count_words(text) < max_size * 0.8:
            return [text]

        # 按标题分割，保持"标题+内容"作为最小单元
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

        # 智能合并section_blocks
        chunks = []
        current_chunk = ""
        current_word_count = 0

        for block in section_blocks:
            block_word_count = self._count_words(block)
            if current_word_count + block_word_count <= max_size:
                current_chunk += block
                current_word_count += block_word_count
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = block
                current_word_count = block_word_count

        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks
```

#### **main.py：主流程示例**

```python
from typing import Optional
from chunker import Chunker
from translator import Translator
from summarizer import Summarizer

def translate_file(
    input_file: str,
    output_file: str,
    model: str = "deepseek-v3",
    large_chunk_size: int = 20000,
    small_chunk_size: int = 2000,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    log_dir: str = "logs"
) -> None:
    """
    翻译Markdown文件，同时保持其结构。
    使用两级分段策略：先按大块生成摘要，再按小块进行翻译。
    """
    chunker = Chunker(large_chunk_size=large_chunk_size, small_chunk_size=small_chunk_size)
    translator = Translator(api_key=api_key, api_base=api_base, default_model=model)
    summarizer = Summarizer(api_key=api_key, api_base=api_base)
    translator.logger.log_dir = log_dir

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 首轮（大块）分段
    word_count = chunker._count_words(content)
    if word_count <= large_chunk_size:
        large_chunks = [content]
    else:
        large_chunks = chunker.split_for_summary(content)

    all_translated_chunks = []
    for large_chunk in large_chunks:
        # 1. 生成摘要
        summary = summarizer.summarize(large_chunk)
        
        # 2. 二次分段（小块，用于翻译）
        small_chunks = chunker.split_for_translation(large_chunk)
        
        # 3. 翻译每个小块
        translated_chunks = translator.translate_batch(small_chunks, summary=summary)
        all_translated_chunks.extend(translated_chunks)

    # 将翻译结果合并并写入文件
    final_text = "\n\n".join(all_translated_chunks)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)
```

#### **评分 Prompt（简要示例）**

```plaintext
你是一位专业的译文审校员。请对以下原文与译文进行比对，根据以下五个维度评分（每个维度0~10分），并输出JSON格式的结果：

维度：
1. accuracy (准确性)
2. completeness (完整性)
3. fluency (流畅性)
4. terminology (术语与用词)
5. style (风格与语气)

**请输出如下JSON，不要输出多余文字**：
{
  "accuracy": 10,
  "accuracy_comment": "示例评语",
  "completeness": 10,
  "completeness_comment": "示例评语",
  "fluency": 10,
  "fluency_comment": "示例评语",
  "terminology": 10,
  "terminology_comment": "示例评语",
  "style": 10,
  "style_comment": "示例评语",
  "total_score": 50,
  "overall_comment": "示例评语"
}

以下是原文：
---
{source_text}
---

以下是译文：
---
{translated_text}
---
```

#### **评分结果解析示例 (Python)**

```python
import json

def parse_rating_response(model_response: str) -> dict:
    """
    model_response: 预期为符合上面JSON格式的字符串
    return: Python字典，包含各维度评分和总分等
    """
    try:
        data = json.loads(model_response)
        # 可以增加字段校验
        return data
    except json.JSONDecodeError:
        # 解析失败
        return {}
```

#### **在代码层面做分数判断并决定是否润色**

```python
def process_translation_block(source_text: str, translated_text: str) -> str:
    """
    如果评分>=45 分，则直接返回译文；否则，将原文、译文和评分结果交给模型润色后再返回。
    """
    # 1. 构造评分请求给 LLM
    rating_prompt = f"""
    你是一位专业的译文审校员。请对以下原文与译文进行比对...
    ...输出JSON格式结果(省略)...
    原文:
    ---
    {source_text}
    ---
    译文:
    ---
    {translated_text}
    ---
    """
    model_response = call_llm_api(rating_prompt)
    
    # 2. 解析JSON评分
    rating_result = parse_rating_response(model_response)
    total_score = rating_result.get("total_score", 0)
    
    # 3. 判断是否需要润色
    if total_score >= 45:
        # 分数合格，无需润色
        return translated_text
    else:
        # 分数不合格，将原文、译文、评分结果交给后续模型润色
        revise_prompt = f"""
        以下是原文：
        ---
        {source_text}
        ---
        现有译文：
        ; ---
        {translated_text}
        ---
        以下是评分结果：
        {json.dumps(rating_result, ensure_ascii=False, indent=2)}

        请基于以上信息，对译文进行润色，特别针对评分结果中提到的问题做改进。
        """
        revised_translation = call_llm_api(revise_prompt)
        return revised_translation
```