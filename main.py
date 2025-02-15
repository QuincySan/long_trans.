"""
Markdown翻译应用程序的主入口。
支持两级分段策略：先生成摘要，再进行翻译。
"""
import os
import argparse
from typing import Optional, List, Dict, Tuple
from chunker import Chunker
from translator import Translator
from summarizer import Summarizer
from utils.markdown_parser import MarkdownParser

def process_large_chunk(
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    chunker: Chunker,
    translator: Translator,
    summarizer: Summarizer
) -> List[str]:
    """
    处理一个大块文本（约20,000词）：生成摘要，然后分成小块翻译。
    
    参数：
        chunk: 大块文本
        chunk_index: 当前块索引
        total_chunks: 总块数
        chunker: 分段器实例
        translator: 翻译器实例
        summarizer: 摘要生成器实例
        
    返回：
        翻译后的文本块列表
    """
    print(f"\n=== 处理第 {chunk_index}/{total_chunks} 个大块 ===")
    
    # 1. 为当前大块生成摘要
    print("生成摘要...")
    summary = summarizer.summarize(chunk)
    print(f"摘要生成完成，长度：{len(summary)}字")
    
    # 2. 将大块分成小块（约2,000词）
    print("进行第二级分段（约2,000词/段）...")
    small_chunks = chunker.split_for_translation(chunk)
    print(f"当前大块分为 {len(small_chunks)} 个小段")
    
    # 3. 使用摘要作为上下文翻译所有小块
    print("开始翻译...")
    translated_chunks = translator.translate_batch(small_chunks, summary=summary)
    
    return translated_chunks

def translate_file(
    input_file: str,
    model: str,
    output_file: Optional[str] = None,
    large_chunk_size: int = 20000,
    small_chunk_size: int = 2000,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    log_dir: str = "logs"
) -> None:
    """
    翻译Markdown文件，同时保持其结构。
    使用两级分段策略：先按大块生成摘要，再按小块进行翻译。
    
    参数：
        input_file: 输入Markdown文件的路径（相对于articles目录）
        model: 选择的模型
        output_file: 输出文件的路径（默认：input_file_translated.md）
        large_chunk_size: 大块的最大单词数（用于摘要）
        small_chunk_size: 小块的最大单词数（用于翻译）
        api_key: LLM服务的API密钥
        api_base: LLM服务的API基础URL
        log_dir: 日志文件保存目录
    """
    # 确保articles目录存在
    articles_dir = "articles"
    if not os.path.exists(articles_dir):
        os.makedirs(articles_dir)
    
    # 构建完整的输入文件路径
    input_path = os.path.join(articles_dir, input_file)
    print(f"\n开始处理文件: {input_path}")
    
    # 设置输出文件名和路径
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_translated{ext}"
    output_path = os.path.join(articles_dir, output_file)

    # 初始化组件
    print("初始化组件...")
    chunker = Chunker(large_chunk_size=large_chunk_size, small_chunk_size=small_chunk_size)
    translator = Translator(api_key=api_key, api_base=api_base)
    summarizer = Summarizer(api_key=api_key, api_base=api_base)
    translator.logger.log_dir = log_dir  # 设置日志目录
    parser = MarkdownParser()

    # 读取输入文件
    print("读取输入文件...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分析文档结构
    print("分析文档结构...")
    headers = parser.get_headers(content)
    code_blocks = parser.get_code_blocks(content)

    # 第一级分段（约20,000词/段）
    print("进行第一级分段（约20,000词/段）...")
    word_count = chunker._count_words(content)
    if word_count <= large_chunk_size:
        print("文档长度不超过20,000词，无需首轮分段")
        large_chunks = [content]
    else:
        large_chunks = chunker.split_for_summary(content)
    print(f"文档分为 {len(large_chunks)} 个大段")

    # 处理每个大段（生成摘要、二次分段、翻译）
    all_translated_chunks = []
    for i, large_chunk in enumerate(large_chunks, 1):
        translated_chunks = process_large_chunk(
            chunk=large_chunk,
            chunk_index=i,
            total_chunks=len(large_chunks),
            chunker=chunker,
            translator=translator,
            summarizer=summarizer
        )
        all_translated_chunks.extend(translated_chunks)

    # 合并所有翻译结果
    print("\n合并所有翻译结果...")
    final_text = '\n\n'.join(all_translated_chunks)

    # 保存结果
    print(f"保存翻译结果到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"\n翻译完成！")
    print(f"- 输入文件：{input_path}")
    print(f"- 输出文件：{output_path}")
    print(f"- 翻译日志：{translator.logger.current_log_file}")

def main():
    """解析命令行参数并运行翻译器。"""
    parser = argparse.ArgumentParser(
        description='翻译Markdown文件，同时保持格式。使用两级分段策略：先生成摘要，再进行翻译。'
    )
    
    parser.add_argument(
        'input_file',
        help='输入Markdown文件的路径（相对于articles目录）'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出文件的路径（相对于articles目录，默认：input_file_translated.md）',
        default=None
    )
    
    parser.add_argument(
        '--large-chunk-size',
        help='大块的最大单词数（用于摘要，默认：20000）',
        type=int,
        default=20000
    )
    
    parser.add_argument(
        '--small-chunk-size',
        help='小块的最大单词数（用于翻译，默认：2000）',
        type=int,
        default=2000
    )
    
    parser.add_argument(
        '-k', '--api-key',
        help='LLM服务的API密钥',
        default=None
    )
    
    parser.add_argument(
        '-b', '--api-base',
        help='LLM服务的API基础URL',
        default=None
    )
    
    parser.add_argument(
        '-l', '--log-dir',
        help='日志文件保存目录（默认：logs）',
        default='logs'
    )

    parser.add_argument(
        '--model',
        help='选择使用的模型 (claude-3-5-sonnet-20241022, deepseek-v3, gemini-2.0-pro-exp-02-05)',
        default="deepseek-v3"
    )

    args = parser.parse_args()

    try:
        translate_file(
            input_file=args.input_file,
            model=args.model,
            output_file=args.output,
            large_chunk_size=args.large_chunk_size,
            small_chunk_size=args.small_chunk_size,
            api_key=args.api_key,
            api_base=args.api_base,
            log_dir=args.log_dir
        )
    except Exception as e:
        print(f"错误：{str(e)}")
        exit(1)

if __name__ == '__main__':
    main() 