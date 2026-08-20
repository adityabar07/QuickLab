import os
import shutil
import tempfile
import pytest
from server.session_manager import SessionManager

@pytest.fixture
def temp_sandbox():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_session_creation_and_directory(temp_sandbox):
    mgr = SessionManager(base_sandbox_dir=temp_sandbox)
    session = mgr.get_or_create("custom_sess_1")
    assert session.session_id == "custom_sess_1"
    assert os.path.exists(session.sandbox_dir)

def test_session_variable_persistence(temp_sandbox):
    mgr = SessionManager(base_sandbox_dir=temp_sandbox)
    session = mgr.get_or_create("pers_sess_1")

    # Cell 1: define a
    outputs1, vars1, count1 = session.execute("a = 42")
    assert count1 == 1
    assert any(v["name"] == "a" and v["preview"] == "42" for v in vars1)

    # Cell 2: use a
    outputs2, vars2, count2 = session.execute("b = a * 2\nprint(b)")
    assert count2 == 2
    assert any(o.get("kind") == "stream" and "84" in o.get("text", "") for o in outputs2)
    assert any(v["name"] == "b" and v["preview"] == "84" for v in vars2)

def test_session_file_upload_and_delete(temp_sandbox):
    mgr = SessionManager(base_sandbox_dir=temp_sandbox)
    session_id = "files_sess_1"
    
    # Save file
    content = b"header1,header2\nval1,val2\n"
    saved_path = mgr.save_file(session_id, "test_data.csv", content)
    assert os.path.exists(saved_path)

    # List files
    files = mgr.list_files(session_id)
    assert len(files) == 1
    assert files[0]["name"] == "test_data.csv"
    assert files[0]["size"] == len(content)

    # Delete file
    deleted = mgr.delete_file(session_id, "test_data.csv")
    assert deleted is True
    assert len(mgr.list_files(session_id)) == 0

def test_clean_inactive_sessions(temp_sandbox):
    mgr = SessionManager(base_sandbox_dir=temp_sandbox)
    s = mgr.get_or_create("old_idle_sess")
    s.last_active = 0 # force old timestamp
    mgr.clean_inactive_sessions(max_idle_seconds=10)
    assert mgr.get("old_idle_sess") is None
