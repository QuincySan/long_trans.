import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


def test_main_calls_process_files(monkeypatch):
    called = {}
    def dummy_process_files(**kwargs):
        called.update(kwargs)
    monkeypatch.setattr(main, 'process_files', dummy_process_files)
    monkeypatch.setattr(main, 'ensure_folders_exist', lambda x: None)
    monkeypatch.setattr(sys, 'argv', ['prog', '--input-folder', 'in', '--output-folder', 'out', '--file', 'a.md'])
    main.main()
    assert called['files'] == ['a.md']
    assert called['input_folder'] == 'in'
    assert called['output_folder'] == 'out'
