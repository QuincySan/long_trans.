import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.translation_logger import TranslationLogger

def test_set_log_dir_updates_file(tmp_path):
    logger = TranslationLogger(log_dir=tmp_path / "old")
    old_file = logger.current_log_file
    new_dir = tmp_path / "new"
    logger.set_log_dir(str(new_dir))
    assert os.path.dirname(logger.current_log_file) == str(new_dir)
    logger.log_segment(
        original_text="a",
        translated_text="b",
        segment_index=1,
        total_segments=1,
    )
    assert os.path.exists(logger.current_log_file)
    assert logger.current_log_file != str(old_file)

