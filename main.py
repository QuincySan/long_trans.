"""
Main entry point for the Markdown translator application.
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
    api_base: Optional[str] = None
) -> None:
    """
    Translate a Markdown file while preserving its structure.
    
    Args:
        input_file: Path to input Markdown file
        output_file: Path to output file (default: input_file_translated.md)
        chunk_size: Maximum size of each chunk for translation
        api_key: Optional API key for the translation service
        api_base: Optional API base URL for the translation service
    """
    # 设置输出文件名
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_translated{ext}"

    # 初始化组件
    chunker = Chunker(max_chunk_size=chunk_size)
    translator = Translator(api_key=api_key, api_base=api_base)
    parser = MarkdownParser()

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分析文档结构
    headers = parser.get_headers(content)
    code_blocks = parser.get_code_blocks(content)

    # 分段
    chunks = chunker.split_text(content)

    # 翻译
    translated_chunks = translator.translate_batch(chunks)

    # 合并结果
    final_text = '\n\n'.join(translated_chunks)

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"Translation completed. Output saved to: {output_file}")

def main():
    """Parse command line arguments and run the translator."""
    parser = argparse.ArgumentParser(
        description='Translate Markdown files while preserving formatting.'
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the input Markdown file'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Path to the output file (default: input_file_translated.md)',
        default=None
    )
    
    parser.add_argument(
        '-s', '--chunk-size',
        help='Maximum size of each chunk for translation (default: 5000)',
        type=int,
        default=5000
    )
    
    parser.add_argument(
        '-k', '--api-key',
        help='API key for the translation service',
        default=None
    )
    
    parser.add_argument(
        '-b', '--api-base',
        help='API base URL for the translation service',
        default=None
    )

    args = parser.parse_args()

    try:
        translate_file(
            input_file=args.input_file,
            output_file=args.output,
            chunk_size=args.chunk_size,
            api_key=args.api_key,
            api_base=args.api_base
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main() 