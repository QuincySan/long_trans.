"""
该模块提供翻译质量评分和润色功能。
用于高质量翻译模式下的自动评分和优化。
"""
from typing import Dict, Optional, Any, Iterator
import json
from llm_client import ZetaClient

class TranslationReviewer:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, score_threshold: int = 48):
        """
        初始化翻译审校器。
        
        参数：
            api_key: LLM服务的API密钥
            api_base: LLM服务的API基础URL
            score_threshold: 评分阈值，低于此分数需要润色（默认48分）
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)
        self.score_threshold = score_threshold
        # 设置不同任务使用的模型
        self.rating_model = "claude-3-5-sonnet-20241022"  # 评分模型使用 Sonnet 3.5
        self.polish_model = "deepseek-v3"  # 润色模型使用 DeepSeek V3

    def rate_translation(self, source_text: str, translated_text: str) -> Dict[str, Any]:
        """
        对翻译结果进行评分。
        
        参数：
            source_text: 原文
            translated_text: 译文
            
        返回：
            包含评分和评语的字典
        """
        prompt = f"""你是一位专业的译文审校员。请对以下原文与译文进行比对，根据以下五个维度评分（每个维度0~10分），并输出JSON格式的结果：

维度：
1. accuracy (准确性)
2. completeness (完整性)
3. fluency (流畅性)
4. terminology (术语与用词)
5. style (风格与语气)

**请输出如下JSON，不要输出多余文字**：
{{
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
}}

以下是原文：
---
{source_text}
---

以下是译文：
---
{translated_text}
---"""

        response = self.llm_client.generate_text(
            prompt=prompt,
            stream=False,
            model=self.rating_model
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果解析失败，返回一个默认的评分结果
            return {
                "accuracy": 0,
                "accuracy_comment": "评分结果解析失败",
                "completeness": 0,
                "completeness_comment": "评分结果解析失败",
                "fluency": 0,
                "fluency_comment": "评分结果解析失败",
                "terminology": 0,
                "terminology_comment": "评分结果解析失败",
                "style": 0,
                "style_comment": "评分结果解析失败",
                "total_score": 0,
                "overall_comment": "评分结果解析失败"
            }

    def polish_translation(self, source_text: str, translated_text: str, rating_result: Dict[str, Any]) -> Iterator[str]:
        """
        根据评分结果对译文进行润色。
        
        参数：
            source_text: 原文
            translated_text: 译文
            rating_result: 评分结果
            
        返回：
            润色后的译文的流式输出迭代器
            
        异常：
            TranslationReviewError: 润色过程出错
        """
        # 构建问题重点提示
        low_score_aspects = []
        for aspect in ["accuracy", "completeness", "fluency", "terminology", "style"]:
            if rating_result.get(aspect, 10) < 7:  # 低于7分的维度需要特别关注
                low_score_aspects.append(f"- {aspect}: {rating_result.get(f'{aspect}_comment', '需要改进')}")
        
        focus_areas = "\n".join(low_score_aspects) if low_score_aspects else "整体质量尚可，建议进行微调优化"
        
        prompt = f"""作为一位资深的翻译专家，请基于以下信息对译文进行润色和改进：

原文：
---
{source_text}
---

当前译文：
---
{translated_text}
---

评分结果：
{json.dumps(rating_result, ensure_ascii=False, indent=2)}

需要重点改进的方面：
{focus_areas}

请重点关注评分中指出的问题，对译文进行优化。要求：
1. 保持原有的Markdown格式和结构
2. 确保专业术语的准确性和一致性
3. 提高语言的流畅度和自然度
4. 符合中文的表达习惯
5. 直接输出优化后的译文，不要添加任何解释

优化后的译文："""

        try:
            # 使用流式输出
            return self.llm_client.generate_text(
                prompt=prompt,
                stream=True,
                model=self.polish_model
            )
        except Exception as e:
            raise TranslationReviewError(f"润色过程出错: {str(e)}")

    def review_and_polish(self, source_text: str, translated_text: str) -> tuple[str, Dict[str, Any]]:
        """
        评分并在需要时进行润色。
        
        参数：
            source_text: 原文
            translated_text: 译文
            
        返回：
            (最终译文, 评分结果) 的元组
        """
        # 1. 评分
        print("\n正在评估译文质量...")
        rating_result = self.rate_translation(source_text, translated_text)
        total_score = rating_result.get("total_score", 0)
        print(f"评分完成！总分：{total_score}/50")
        
        # 2. 判断是否需要润色
        if total_score >= self.score_threshold:
            print("译文质量良好，无需润色。")
            return translated_text, rating_result
        
        # 3. 润色（流式输出）
        print(f"\n译文质量低于阈值（{self.score_threshold}分），开始润色...")
        polished_text_parts = []
        for chunk in self.polish_translation(source_text, translated_text, rating_result):
            print(chunk, end="", flush=True)
            polished_text_parts.append(chunk)
        
        polished_text = "".join(polished_text_parts)
        print("\n\n润色完成！")
        
        return polished_text, rating_result

class TranslationReviewError(Exception):
    """润色过程中的错误"""
    pass 