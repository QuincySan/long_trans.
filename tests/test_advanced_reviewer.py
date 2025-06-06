import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import advanced_reviewer


def test_comment_and_polish(monkeypatch):
    class DummyClient:
        def __init__(self, *a, **k):
            pass
        def generate_text(self, prompt, model=None, system_prompt=""):
            if "请仔细阅读" in prompt:
                return "comments"
            return "polished"
    monkeypatch.setattr(advanced_reviewer, 'ZetaClient', DummyClient)
    ar = advanced_reviewer.AdvancedReviewer()
    text, comments = ar.comment_and_polish("src", "tran")
    assert text == "polished"
    assert comments == "comments"
    assert ar.get_latest_results() == ("polished", "comments")
