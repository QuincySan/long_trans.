import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chunker import Chunker


def test_count_words_mixed():
    c = Chunker()
    # \w 也会匹配中文字符，因此英文单词+中文字符共计4词
    assert c._count_words("Hello 世界") == 4


def test_split_for_translation_respects_size():
    text = "# T\n\n" + "word " * 10
    c = Chunker(large_chunk_size=50, small_chunk_size=3)
    chunks = c.split_for_translation(text)
    assert len(chunks) >= 2
