"""
Markdown翻译应用程序的主入口。
"""
import os
import argparse
from typing import Optional
from chunker import Chunker
from translator import Translator
from utils.markdown_parser import MarkdownParser

def translate_file(
    input_file: str,
    output_file: Optional[str] = None,
    chunk_size: int = 5000,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    log_dir: str = "logs"
) -> None:
    """
    翻译Markdown文件，同时保持其结构。
    
    参数：
        input_file: 输入Markdown文件的路径
        output_file: 输出文件的路径（默认：input_file_translated.md）
        chunk_size: 每个块的最大字符数
        api_key: 翻译服务的可选API密钥
        api_base: 翻译服务的可选API基础URL
        log_dir: 日志文件保存目录
    """
    print(f"\n开始处理文件: {input_file}")
    
    # 设置输出文件名
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_translated{ext}"

    # 初始化组件
    print("初始化组件...")
    chunker = Chunker(max_chunk_size=chunk_size)
    translator = Translator(api_key=api_key, api_base=api_base)
    translator.logger.log_dir = log_dir  # 设置日志目录
    parser = MarkdownParser()

    # 读取输入文件
    print("读取输入文件...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分析文档结构
    print("分析文档结构...")
    headers = parser.get_headers(content)
    code_blocks = parser.get_code_blocks(content)

    # 分段
    print("将文档分段...")
    chunks = chunker.split_text(content)
    print(f"文档已分为 {len(chunks)} 段")

    # 翻译
    print("\n开始翻译过程...")
    translated_chunks = translator.translate_batch(chunks)

    # 合并结果
    print("\n合并翻译结果...")
    final_text = '\n\n'.join(translated_chunks)

    # 保存结果
    print(f"保存翻译结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"\n翻译完成！")
    print(f"- 输出文件：{output_file}")
    print(f"- 翻译日志：{translator.logger.current_log_file}")

def main():
    """解析命令行参数并运行翻译器。"""
    parser = argparse.ArgumentParser(
        description='翻译Markdown文件，同时保持格式。'
    )
    
    parser.add_argument(
        'input_file',
        help='输入Markdown文件的路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出文件的路径（默认：input_file_translated.md）',
        default=None
    )
    
    parser.add_argument(
        '-s', '--chunk-size',
        help='每个块的最大字符数（默认：5000）',
        type=int,
        default=5000
    )
    
    parser.add_argument(
        '-k', '--api-key',
        help='翻译服务的API密钥',
        default=None
    )
    
    parser.add_argument(
        '-b', '--api-base',
        help='翻译服务的API基础URL',
        default=None
    )
    
    parser.add_argument(
        '-l', '--log-dir',
        help='日志文件保存目录（默认：logs）',
        default='logs'
    )

    args = parser.parse_args()

    try:
        translate_file(
            input_file=args.input_file,
            output_file=args.output,
            chunk_size=args.chunk_size,
            api_key=args.api_key,
            api_base=args.api_base,
            log_dir=args.log_dir
        )
    except Exception as e:
        print(f"错误：{str(e)}")
        exit(1)

if __name__ == '__main__':
    main() 