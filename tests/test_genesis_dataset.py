"""Genesis instruction dataset generator tests."""
from __future__ import annotations

from pathlib import Path

from om_ai.genesis import write_dataset
from om_ai.training.sft import _row_to_messages
import json


def test_write_small_dataset(tmp_path: Path):
    out = tmp_path / "g.jsonl"
    man = write_dataset(out, count=25)
    assert man["count"] == 25
    line = out.read_text(encoding="utf-8").splitlines()[0]
    row = json.loads(line)
    msgs, resp = _row_to_messages(row)
    assert msgs and resp
    assert "Horizon" in resp or "Understanding" in resp or "Explanation" in resp
