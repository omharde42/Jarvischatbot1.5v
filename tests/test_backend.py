import pytest
import asyncio
import os
import subprocess
from fastapi.testclient import TestClient
from server import app
from app.safety import safety_engine, RiskLevel
from app.intent import IntentParser, parse_and_execute
from skills import system, filesystem, developer, git, productivity

client = TestClient(app)

def test_health_and_telemetry():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "telemetry" in data
    assert "cpu_percent" in data["telemetry"]

def test_safety_classification():
    assert safety_engine.classify_action("list_files", {}) == RiskLevel.LOW
    assert safety_engine.classify_action("start_dev_server", {}) == RiskLevel.MEDIUM
    assert safety_engine.classify_action("stop_dev_server", {}) == RiskLevel.MEDIUM
    assert safety_engine.classify_action("delete_file", {}) == RiskLevel.HIGH

def test_intent_parser():
    parsed_cpu = IntentParser.parse("What is using the most CPU?")
    assert parsed_cpu["intent"] == "get_top_cpu"

    parsed_files = IntentParser.parse("What files are in this folder?")
    assert parsed_files["intent"] == "list_files"

    parsed_create = IntentParser.parse("Create a new folder called Projects")
    assert parsed_create["intent"] == "create_folder"
    assert parsed_create["args"]["folder_name"] == "Projects"

    parsed_named_folder = IntentParser.parse("Create a new folder named Notes")
    assert parsed_named_folder["args"]["folder_name"] == "Notes"

    parsed_called_file = IntentParser.parse("Create a file called notes.txt")
    assert parsed_called_file["args"]["filepath"] == "notes.txt"

    parsed_named_file = IntentParser.parse("Create a file named tasks.txt")
    assert parsed_named_file["args"]["filepath"] == "tasks.txt"

    parsed_delete = IntentParser.parse("Delete file test.txt")
    assert parsed_delete["intent"] == "delete_file"
    assert parsed_delete["args"]["target_path"] == "test.txt"

def test_skills_filesystem(tmp_path):
    test_dir = tmp_path / "test_dir"
    folder_res = filesystem.create_folder(str(test_dir))
    assert folder_res["success"] is True

    file_path = test_dir / "sample.txt"
    create_res = filesystem.create_file(str(file_path), "Hello JARVIS")
    assert create_res["success"] is True

    overwrite_res = filesystem.create_file(str(file_path), "Unexpected overwrite")
    assert overwrite_res["success"] is False
    assert file_path.read_text() == "Hello JARVIS"

    read_res = filesystem.read_file(str(file_path))
    assert read_res["success"] is True
    assert "Hello JARVIS" in read_res["content"]

    del_res = filesystem.delete_path(str(file_path))
    assert del_res["success"] is True

@pytest.mark.asyncio
async def test_high_risk_confirmation_flow(tmp_path):
    test_file = tmp_path / "delete_me.txt"
    filesystem.create_file(str(test_file), "Delete me")

    res = await parse_and_execute(f"Delete file {test_file}")
    assert res["requires_confirmation"] is True
    token = res["confirmation_token"]

    confirm_res = safety_engine.process_confirmation(token, confirmed=True)
    assert confirm_res["success"] is True
    assert not test_file.exists()

@pytest.mark.asyncio
async def test_existing_file_requires_overwrite_confirmation(tmp_path):
    test_file = tmp_path / "keep_me.txt"
    test_file.write_text("Keep this content")

    res = await parse_and_execute(f"Create a file called {test_file}")

    assert res["requires_confirmation"] is True
    assert res["risk_level"] == RiskLevel.HIGH
    assert test_file.read_text() == "Keep this content"

    confirm_res = safety_engine.process_confirmation(
        res["confirmation_token"],
        confirmed=True,
    )
    assert confirm_res["success"] is True
    assert test_file.read_text() == ""

def test_search_code_stops_at_match_limit(tmp_path):
    for index in range(2):
        (tmp_path / f"source_{index}.py").write_text("needle\n" * 40)

    result = developer.search_code("needle", str(tmp_path))

    assert result["success"] is True
    assert len(result["matches"]) == 30

def test_start_dev_server_uses_direct_process_arguments(monkeypatch):
    captured = {}

    class FakeProcess:
        pid = 1234

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(developer, "active_dev_servers", {})

    result = developer.start_dev_server("python3 -m http.server")

    assert result["success"] is True
    assert captured["args"] == ["python3", "-m", "http.server"]
    assert captured["kwargs"] == {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }

def test_stop_dev_server_targets_matching_command(monkeypatch):
    killed = []
    monkeypatch.setattr(
        developer,
        "active_dev_servers",
        {"server one": 101, "server two": 202},
    )
    monkeypatch.setattr(os, "kill", lambda pid, signal: killed.append((pid, signal)))

    result = developer.stop_dev_server("server one")

    assert result["success"] is True
    assert killed == [(101, 9)]
    assert developer.active_dev_servers == {"server two": 202}
