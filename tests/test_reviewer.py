import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reviewer


def test_rate_translation_invalid_json(monkeypatch):
    class DummyClient:
        def __init__(self, *a, **k):
            pass
        def generate_text(self, *a, **k):
            return "not json"
    monkeypatch.setattr(reviewer, 'ZetaClient', DummyClient)
    r = reviewer.TranslationReviewer()
    result = r.rate_translation("src", "trans")
    assert result["total_score"] == 0
