from conftest import ADMIN_EMAIL, ADMIN_PASSWORD
from fastapi.testclient import TestClient


def test_login_success_sets_httponly_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    assert response.json() == {"email": ADMIN_EMAIL}
    set_cookie = response.headers["set-cookie"].lower()
    assert "alma_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "path=/" in set_cookie
    assert "max-age=28800" in set_cookie


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_wrong_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": "impostor@test.com", "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 401


def test_me_unauthenticated_returns_401(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_with_session_cookie(auth_client: TestClient) -> None:
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"email": ADMIN_EMAIL}


def test_garbage_cookie_rejected(client: TestClient) -> None:
    client.cookies.set("alma_session", "not-a-valid-jwt")
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_logout_clears_cookie(auth_client: TestClient) -> None:
    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 204
    assert auth_client.get("/api/auth/me").status_code == 401
