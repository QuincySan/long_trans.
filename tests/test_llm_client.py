import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import llm_client


class DummyOpenAI:
    def __init__(self, *a, **k):
        pass
    class chat:
        class completions:
            @staticmethod
            def create(*a, **k):
                class Choice:
                    pass
                choice = Choice()
                choice.message = type("obj", (), {"content": "ok"})()
                class R:
                    pass
                res = R()
                res.choices = [choice]
                return res


def test_fireworks_client_requires_key(monkeypatch):
    monkeypatch.setattr(llm_client, 'OpenAI', DummyOpenAI)
    monkeypatch.delenv('FIREWORKS_API_KEY', raising=False)
    with pytest.raises(ValueError):
        llm_client.FireworksClient(api_key=None)


def test_zeta_client_invalid_model(monkeypatch):
    monkeypatch.setattr(llm_client, 'OpenAI', DummyOpenAI)
    client = llm_client.ZetaClient(api_key='x')
    with pytest.raises(ValueError):
        client.generate_text('hi', model='bad-model')
