"""
Markdown翻译应用程序的主入口。
支持两级分段策略：先生成摘要，再进行翻译。
支持单文件和批量翻译，统一使用指定文件夹。
"""
import os
import shutil
import argparse
from typing import Optional, List, Dict, Tuple
from chunker import Chunker
from translator import Translator
from summarizer import Summarizer
from utils.markdown_parser import MarkdownParser

# 默认目录配置
DEFAULT_INPUT_FOLDER = "to_translate"
DEFAULT_OUTPUT_FOLDER = "translated"
DEFAULT_LOG_FOLDER = "logs"

def ensure_folders_exist(folders: List[str]) -> None:
    """
    确保指定的文件夹存在，如果不存在则创建。
    
    参数：
        folders: 需要确保存在的文件夹路径列表
    """
    for folder in folders:
        if not os.path.exists(folder):
            print(f"[提示] 创建文件夹：{folder}")
            os.makedirs(folder)

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
    log_dir: str = "logs",
    quality_level: str = "basic"
) -> None:
    """
    翻译Markdown文件，同时保持其结构。
    使用两级分段策略：先按大块生成摘要，再按小块进行翻译。
    
    参数：
        input_file: 输入Markdown文件的完整路径
        model: 选择的模型
        output_file: 输出文件的完整路径
        large_chunk_size: 大块的最大单词数（用于摘要）
        small_chunk_size: 小块的最大单词数（用于翻译）
        api_key: LLM服务的API密钥
        api_base: LLM服务的API基础URL
        log_dir: 日志文件保存目录
        quality_level: 翻译质量等级，可选值：basic（基础）, advanced（高级）
    """
    print(f"\n开始处理文件: {input_file}")
    
    # 初始化组件
    print("初始化组件...")
    chunker = Chunker(large_chunk_size=large_chunk_size, small_chunk_size=small_chunk_size)
    translator = Translator(api_key=api_key, api_base=api_base, quality_level=quality_level)
    summarizer = Summarizer(api_key=api_key, api_base=api_base)
    translator.logger.set_log_dir(log_dir)  # 设置日志目录
    parser = MarkdownParser()

    # 读取输入文件
    print("读取输入文件...")
    with open(input_file, 'r', encoding='utf-8') as f:
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
    print(f"保存翻译结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"\n翻译完成！")
    print(f"- 输入文件：{input_file}")
    print(f"- 输出文件：{output_file}")
    print(f"- 翻译日志：{translator.logger.current_log_file}")

def process_files(
    files: List[str],
    input_folder: str = DEFAULT_INPUT_FOLDER,
    output_folder: str = DEFAULT_OUTPUT_FOLDER,
    model: str = "deepseek-v3",
    large_chunk_size: int = 20000,
    small_chunk_size: int = 2000,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    log_dir: str = "logs",
    quality_level: str = "basic"
) -> None:
    """
    处理指定的一个或多个Markdown文件。
    
    参数：
        files: 要处理的文件名列表
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径
        model: 选择的模型
        large_chunk_size: 大块的最大单词数（用于摘要）
        small_chunk_size: 小块的最大单词数（用于翻译）
        api_key: LLM服务的API密钥
        api_base: LLM服务的API基础URL
        log_dir: 日志文件保存目录
        quality_level: 翻译质量等级，可选值：basic（基础）, advanced（高级）
    """
    # 确保所有必要的文件夹都存在
    ensure_folders_exist([input_folder, output_folder, log_dir])

    if len(files) == 0:
        print(f"[提示] 在文件夹 '{input_folder}' 中未找到Markdown文件。")
        return

    print(f"\n=== 开始翻译，共 {len(files)} 个Markdown文件 ===\n")
    
    for index, file_name in enumerate(files, 1):
        input_path = os.path.join(input_folder, file_name)
        if not os.path.exists(input_path):
            print(f"[错误] 文件不存在: {input_path}")
            continue
            
        base, ext = os.path.splitext(file_name)
        translated_file_name = f"{base}_translated{ext}"
        output_path = os.path.join(output_folder, translated_file_name)

        print(f"\n[{index}/{len(files)}] 正在翻译: {file_name}")
        try:
            translate_file(
                input_file=input_path,
                model=model,
                output_file=output_path,
                large_chunk_size=large_chunk_size,
                small_chunk_size=small_chunk_size,
                api_key=api_key,
                api_base=api_base,
                log_dir=log_dir,
                quality_level=quality_level
            )

            # 将原文件移动到输出文件夹
            original_file_new_path = os.path.join(output_folder, file_name)
            shutil.move(input_path, original_file_new_path)
            print(f"[完成] 已移动原文件并保存翻译结果：{file_name} -> {translated_file_name}")

        except Exception as e:
            print(f"[错误] 翻译 {file_name} 时出错: {str(e)}")
            continue

    print(f"\n=== 翻译完成！所有结果已保存到 '{output_folder}' 目录 ===")

def main():
    """解析命令行参数并运行翻译器。"""
    parser = argparse.ArgumentParser(
        description='翻译Markdown文件，同时保持格式。支持单文件和批量翻译，统一使用指定文件夹。'
    )
    
    # 文件夹参数
    parser.add_argument(
        '--input-folder',
        help=f'输入文件夹路径（默认：{DEFAULT_INPUT_FOLDER}）',
        default=DEFAULT_INPUT_FOLDER
    )
    
    parser.add_argument(
        '--output-folder',
        help=f'输出文件夹路径（默认：{DEFAULT_OUTPUT_FOLDER}）',
        default=DEFAULT_OUTPUT_FOLDER
    )
    
    # 可选的单文件指定
    parser.add_argument(
        '-f', '--file',
        help='指定要翻译的单个文件名（在输入文件夹中的文件名）',
        default=None
    )
    
    # 通用参数
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
        default=DEFAULT_LOG_FOLDER
    )

    parser.add_argument(
        '--model',
        help='选择使用的模型 (claude-3-5-sonnet-20241022, deepseek-v3, gemini-2.0-pro-exp-02-05)',
        default="deepseek-v3"
    )

    parser.add_argument(
        '--quality',
        help='翻译质量等级 (basic: 基础翻译，适合一般性文档; advanced: 高级翻译，带详细点评和润色。默认：basic)',
        choices=['basic', 'advanced'],
        default='basic'
    )

    args = parser.parse_args()

    try:
        # 确保所有必要的文件夹都存在
        ensure_folders_exist([args.input_folder, args.output_folder, args.log_dir])

        # 获取要处理的文件列表
        if args.file:
            # 单文件模式
            files = [args.file]
        else:
            # 批量模式：处理输入文件夹中的所有.md文件
            if args.quality == "basic":
                print(f"\n[提示] 使用基础翻译等级。如需更高质量翻译，请添加 --quality advanced 参数")
            else:  # advanced
                print(f"\n[提示] 使用高级翻译等级，将对译文进行详细点评和润色")
            files = [f for f in os.listdir(args.input_folder) if f.lower().endswith(".md")]

        process_files(
            files=files,
            input_folder=args.input_folder,
            output_folder=args.output_folder,
            model=args.model,
            large_chunk_size=args.large_chunk_size,
            small_chunk_size=args.small_chunk_size,
            api_key=args.api_key,
            api_base=args.api_base,
            log_dir=args.log_dir,
            quality_level=args.quality
        )
    except Exception as e:
        print(f"错误：{str(e)}")
        exit(1)

if __name__ == '__main__':
    main() 