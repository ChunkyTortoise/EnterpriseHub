from pathlib import Path

from ghl_real_estate_ai.services.auth_service import AuthService


def test_auth_service_uses_env_secret_without_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-for-auth-service-1234567890")

    service = AuthService(db_path=str(tmp_path / "auth.db"))

    assert service.secret_key == "test-jwt-secret-key-for-auth-service-1234567890"
    assert not Path("data/.jwt_secret").exists()


def test_auth_service_generates_process_local_secret_without_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    service = AuthService(db_path=str(tmp_path / "auth.db"))

    assert len(service.secret_key) >= 32
    assert not Path("data/.jwt_secret").exists()
