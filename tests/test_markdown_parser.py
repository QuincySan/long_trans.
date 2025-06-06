import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.markdown_parser import MarkdownParser


def test_extract_headers_and_code_blocks():
    text = "# Title\n\n```py\nprint('hi')\n```"
    parser = MarkdownParser()
    headers = parser.get_headers(text)
    codes = parser.get_code_blocks(text)
    assert headers[0]['level'] == 1
    assert headers[0]['content'] == 'Title'
    assert codes[0]['language'] == 'py'
    assert "print" in codes[0]['content']
