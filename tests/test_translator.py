import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import translator


def setup_dummy(monkeypatch):
    class DummyClient:
        def __init__(self, *a, **k):
            pass
        def generate_text(self, *a, **k):
            return "translated"

    class DummyLogger:
        def __init__(self, *a, **k):
            self.logged = False
        def log_segment(self, *a, **k):
            self.logged = True
        def log_advanced_review(self, *a, **k):
            self.logged = True
        def set_log_dir(self, *a, **k):
            pass

    monkeypatch.setattr(translator, 'ZetaClient', DummyClient)
    monkeypatch.setattr(translator, 'TranslationLogger', DummyLogger)


def test_translate_text_basic(monkeypatch):
    setup_dummy(monkeypatch)
    t = translator.Translator(quality_level="basic")
    result = t.translate_text("hello")
    assert result == "translated"


def test_translate_text_medium(monkeypatch):
    setup_dummy(monkeypatch)
    class DummyReviewer:
        def __init__(self, *a, **k):
            pass
        def review_and_polish(self, src, text):
            return "polished", {"score": 50}
    monkeypatch.setattr(translator, 'TranslationReviewer', DummyReviewer)
    t = translator.Translator(quality_level="medium")
    result = t.translate_text("hello")
    assert result == "polished"


def test_translate_text_advanced(monkeypatch):
    setup_dummy(monkeypatch)
    class DummyAdv:
        def __init__(self, *a, **k):
            pass
        def comment_and_polish(self, src, text):
            return "adv_polish", "comments"
    monkeypatch.setattr(translator, 'AdvancedReviewer', DummyAdv)
    t = translator.Translator(quality_level="advanced")
    result = t.translate_text("hello")
    assert result == "adv_polish"
