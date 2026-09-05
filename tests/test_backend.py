import pytest
import asyncio
from fastapi.testclient import TestClient
from server import app
from app.safety import safety_engine, RiskLevel
from app.intent import IntentParser, parse_and_execute
from skills import system, filesystem, developer, git, productivity
import system_controls
from ai_core import ai_engine

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
    assert safety_engine.classify_action("system_power", {}) == RiskLevel.HIGH

def test_intent_parser():
    parsed_cpu = IntentParser.parse("What is using the most CPU?")
    assert parsed_cpu["intent"] == "get_top_cpu"

    parsed_files = IntentParser.parse("What files are in this folder?")
    assert parsed_files["intent"] == "list_files"

    parsed_create = IntentParser.parse("Create a new folder called Projects")
    assert parsed_create["intent"] == "create_folder"
    assert parsed_create["args"]["folder_name"] == "Projects"

    parsed_create_file = IntentParser.parse("create a file called notes.txt")
    assert parsed_create_file["intent"] == "create_file"
    assert parsed_create_file["args"]["filepath"] == "notes.txt"

    parsed_delete = IntentParser.parse("Delete file test.txt")
    assert parsed_delete["intent"] == "delete_file"
    assert parsed_delete["args"]["target_path"] == "test.txt"

    parsed_yt = IntentParser.parse("open YouTube and search Python tutorials")
    assert parsed_yt["intent"] == "search_youtube"
    assert parsed_yt["args"]["topic"] == "Python tutorials"

    parsed_lock = IntentParser.parse("Lock the phone")
    assert parsed_lock["intent"] == "lock_phone"

    parsed_unlock = IntentParser.parse("Unlock phone")
    assert parsed_unlock["intent"] == "unlock_phone"

def test_skills_filesystem(tmp_path):
    test_dir = tmp_path / "test_dir"
    folder_res = filesystem.create_folder(str(test_dir))
    assert folder_res["success"] is True

    file_path = test_dir / "sample.txt"
    create_res = filesystem.create_file(str(file_path), "Hello JARVIS")
    assert create_res["success"] is True

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
    assert len(token) >= 16

    confirm_res = safety_engine.process_confirmation(token, confirmed=True)
    assert confirm_res["success"] is True
    assert not test_file.exists()

@pytest.mark.asyncio
async def test_create_file_overwrite_confirmation_flow(tmp_path):
    existing_file = tmp_path / "existing.txt"
    filesystem.create_file(str(existing_file), "Original Content")

    res = await parse_and_execute(f"create a file called {existing_file}")
    assert res["requires_confirmation"] is True
    token = res["confirmation_token"]

    confirm_res = safety_engine.process_confirmation(token, confirmed=True)
    assert confirm_res["success"] is True
    assert existing_file.exists()

def test_search_code_30_limit(tmp_path):
    for i in range(40):
        (tmp_path / f"file_{i}.py").write_text("match_keyword line content\n")

    res = developer.search_code("match_keyword", root_dir=str(tmp_path))
    assert res["success"] is True
    assert len(res["matches"]) == 30

def test_dev_server_control():
    start_res = developer.start_dev_server("python3 -m http.server 9999")
    assert start_res["success"] is True

    stop_res = developer.stop_dev_server("python3 -m http.server 9999")
    assert stop_res["success"] is True

@pytest.mark.asyncio
async def test_phone_lock_and_pin_flow():
    lock_res = await parse_and_execute("Lock the phone")
    assert lock_res["success"] is True
    assert system_controls.phone_lock.is_phone_locked is True

    unlock_req = await parse_and_execute("Unlock phone")
    assert unlock_req["success"] is True
    assert "PIN" in unlock_req["spoken_response"]
    assert system_controls.phone_lock.awaiting_pin is True

    # Test incorrect PIN first
    bad_pin_res = await parse_and_execute("9999")
    assert bad_pin_res["success"] is False
    assert "Incorrect PIN" in bad_pin_res["spoken_response"]
    assert system_controls.phone_lock.is_phone_locked is True

    # Test correct PIN
    good_pin_res = await parse_and_execute("1234")
    assert good_pin_res["success"] is True
    assert "unlocked" in good_pin_res["spoken_response"]
    assert system_controls.phone_lock.is_phone_locked is False

def test_youtube_search_formatting():
    res = system_controls.search_youtube("quantum computing explained")
    assert res["success"] is True
    assert "quantum+computing+explained" in res["url"]

def test_ai_core_fallback():
    res = ai_engine.generate_response("What is the speed of light?")
    assert res["success"] is True
    assert "spoken_response" in res
