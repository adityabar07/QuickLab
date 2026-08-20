import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Python" in data["engine"]
    assert data["total_packages"] == 7

def test_packages_endpoint():
    response = client.get("/api/packages")
    assert response.status_code == 200
    data = response.json()
    packages = data["packages"]
    assert len(packages) == 7
    pkg_names = [p["name"] for p in packages]
    for expected in ["numpy", "pandas", "matplotlib", "seaborn", "scipy", "sympy", "scikit-learn"]:
        assert expected in pkg_names

def test_create_and_delete_session():
    # Create
    create_resp = client.post("/api/session")
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]
    assert session_id is not None

    # Delete
    del_resp = client.delete(f"/api/session/{session_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

def test_execute_endpoint():
    code = "import numpy as np\na = np.array([1, 2, 3])\nprint('SUM:', a.sum())"
    response = client.post("/api/execute", json={"code": code, "session_id": "test_api_session"})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_api_session"
    assert data["exec_count"] >= 1
    assert any(o.get("kind") == "stream" and "SUM: 6" in o.get("text", "") for o in data["outputs"])

def test_restart_kernel():
    # Set variable
    client.post("/api/execute", json={"code": "my_secret_var = 12345", "session_id": "restart_test_sess"})
    # Verify variable exists
    var_resp = client.get("/api/variables/restart_test_sess")
    assert any(v["name"] == "my_secret_var" for v in var_resp.json()["variables"])

    # Restart
    restart_resp = client.post("/api/restart", json={"session_id": "restart_test_sess"})
    assert restart_resp.status_code == 200
    assert restart_resp.json()["success"] is True

    # Verify cleared
    var_resp_after = client.get("/api/variables/restart_test_sess")
    assert not any(v["name"] == "my_secret_var" for v in var_resp_after.json()["variables"])
