import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import summarizer


def test_summarize_calls_llm(monkeypatch):
    called = {}

    class DummyClient:
        def __init__(self, *a, **k):
            pass
        def generate_text(self, prompt, model=None, system_prompt="", response_format=None):
            called['prompt'] = prompt
            return "summary"

    monkeypatch.setattr(summarizer, 'ZetaClient', DummyClient)
    s = summarizer.Summarizer()
    result = s.summarize("text")
    assert result == "summary"
    assert "text" in called['prompt']
