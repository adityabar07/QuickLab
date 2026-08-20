import os
import io
import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.config import settings
from scripts.security_check import run_security_scan
from pathlib import Path

client = TestClient(app)

def test_invalid_session_id_rejection():
    invalid_ids = ["..", "../../etc/passwd", "sess\x00null", "ab", "a" * 100, "<script>", "sess;rm -rf /"]
    for sid in invalid_ids:
        res = client.post("/api/execute", json={"code": "print(1)", "session_id": sid})
        assert res.status_code in (400, 422), f"Expected 400 or 422 for session_id '{sid}', got {res.status_code}"

def test_path_traversal_file_operations():
    valid_sid = "test_sec_sess_1"
    traversal_names = ["..%2F..%2Fpasswd.txt", "..%5C..%5Cwin.ini", "subdir/file.csv", "sub\\file.json", "file%00.csv", "nested/secret.txt"]
    
    for fname in traversal_names:
        # Download
        res = client.get(f"/api/files/{valid_sid}/{fname}")
        assert res.status_code in (400, 404), f"Expected 400 or 404 for download path '{fname}', got {res.status_code}"

        # Delete
        del_res = client.delete(f"/api/files/{valid_sid}/{fname}")
        assert del_res.status_code in (400, 404), f"Expected 400 or 404 for delete path '{fname}', got {del_res.status_code}"

def test_disallowed_file_extensions():
    valid_sid = "test_upload_sess_1"
    bad_files = ["malware.exe", "script.py", "exploit.sh", "payload.php", "hack.dll", "image.png"]
    
    for fname in bad_files:
        file_tuple = (fname, io.BytesIO(b"sample data content"), "application/octet-stream")
        res = client.post(
            "/api/files/upload",
            data={"session_id": valid_sid},
            files={"file": file_tuple}
        )
        assert res.status_code == 400, f"Expected 400 for disallowed file '{fname}', got {res.status_code}"
        assert "not allowed" in res.json().get("detail", "").lower()

def test_binary_executable_magic_byte_rejection():
    valid_sid = "test_binary_check_sess"
    # An ELF binary header disguised with .txt extension
    elf_content = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    file_tuple = ("disguised.txt", io.BytesIO(elf_content), "text/plain")
    res = client.post(
        "/api/files/upload",
        data={"session_id": valid_sid},
        files={"file": file_tuple}
    )
    assert res.status_code == 400
    assert "executable" in res.json().get("detail", "").lower()

def test_valid_file_upload_and_cross_session_isolation():
    session_a = "session_iso_user_a"
    session_b = "session_iso_user_b"

    # User A uploads data.csv
    csv_content = b"col1,col2\n10,20\n30,40\n"
    file_tuple = ("data.csv", io.BytesIO(csv_content), "text/csv")
    res_a = client.post(
        "/api/files/upload",
        data={"session_id": session_a},
        files={"file": file_tuple}
    )
    assert res_a.status_code == 200

    # User A sees data.csv
    list_a = client.get(f"/api/files/{session_a}").json()["files"]
    assert any(f["name"] == "data.csv" for f in list_a)

    # User B list does NOT see User A's data.csv
    list_b = client.get(f"/api/files/{session_b}").json()["files"]
    assert not any(f["name"] == "data.csv" for f in list_b)

    # User B cannot download User A's data.csv via User B's session
    res_b_down = client.get(f"/api/files/{session_b}/data.csv")
    assert res_b_down.status_code == 404

    # User B cannot delete User A's data.csv via User B's session
    res_b_del = client.delete(f"/api/files/{session_b}/data.csv")
    assert res_b_del.status_code == 404

def test_rate_limiting_enforcement():
    # Rapidly fire requests to trigger rate limiter
    hit_rate_limit = False
    for _ in range(settings.RATE_LIMIT_SESSION_PER_MIN + 5):
        res = client.post("/api/session")
        if res.status_code == 429:
            hit_rate_limit = True
            assert "Retry-After" in res.headers
            break
    assert hit_rate_limit is True, "Rate limiter should have returned HTTP 429 after exceeding limit."

def test_traceback_sanitization_no_internal_path_disclosure():
    res = client.post(
        "/api/execute",
        json={"code": "1 / 0", "session_id": "test_tb_sanitize"}
    )
    assert res.status_code == 200
    outputs = res.json()["outputs"]
    assert len(outputs) > 0
    err_text = outputs[0]["text"]
    assert "ZeroDivisionError" in err_text
    # Ensure internal server wrapper paths are not leaked
    assert "server/execution.py" not in err_text
    assert "server\\execution.py" not in err_text

def test_repository_secret_scanner():
    base_dir = Path(__file__).resolve().parent.parent
    exit_code = run_security_scan(base_dir)
    assert exit_code == 0, "Security scan found potential secrets or credentials in the repository."
