import pytest
import asyncio
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
    assert safety_engine.classify_action("git_commit", {}) == RiskLevel.MEDIUM
    assert safety_engine.classify_action("delete_file", {}) == RiskLevel.HIGH

def test_intent_parser():
    parsed_cpu = IntentParser.parse("What is using the most CPU?")
    assert parsed_cpu["intent"] == "get_top_cpu"

    parsed_files = IntentParser.parse("What files are in this folder?")
    assert parsed_files["intent"] == "list_files"

    parsed_create = IntentParser.parse("Create a new folder called Projects")
    assert parsed_create["intent"] == "create_folder"
    assert parsed_create["args"]["folder_name"] == "Projects"

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
