import os
from pathlib import Path

from om_ai.env import load_dotenv


def test_load_dotenv_sets_missing_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("OM_AI_TEST_KEY=from_file\nOM_AI_TEST_QUOTED=\"hello world\"\n")
    monkeypatch.delenv("OM_AI_TEST_KEY", raising=False)
    monkeypatch.delenv("OM_AI_TEST_QUOTED", raising=False)
    assert load_dotenv(env) == env
    assert os.environ["OM_AI_TEST_KEY"] == "from_file"
    assert os.environ["OM_AI_TEST_QUOTED"] == "hello world"


def test_load_dotenv_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("OM_AI_TEST_KEEP=from_file\n")
    monkeypatch.setenv("OM_AI_TEST_KEEP", "from_shell")
    load_dotenv(env)
    assert os.environ["OM_AI_TEST_KEEP"] == "from_shell"


def test_load_dotenv_missing_returns_none(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") is None
