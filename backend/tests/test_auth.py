from datetime import timedelta
import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User
from app.config import settings
from app.security import verify_password, create_access_token


def test_user_registration_success(client: TestClient, db_session: Session):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test User",
            "email": "unique_user@example.com",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "unique_user@example.com"
    assert data["full_name"] == "Test User"
    assert "password_hash" not in data  # Sensitive fields must never leak!

    # Verify password was hashed in database
    user = db_session.query(User).filter(User.email == "unique_user@example.com").first()
    assert user is not None
    assert user.password_hash != "SecurePassword123"
    assert user.password_hash.startswith("$argon2")
    assert verify_password("SecurePassword123", user.password_hash) is True


def test_registration_duplicate_email_rejected(client: TestClient, test_user_a: User):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Alice Duplicate",
            "email": "alice@example.com",  # Duplicate email
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_registration_password_mismatch_rejected(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        },
    )
    assert response.status_code == 422


def test_registration_weak_password_rejected(client: TestClient):
    # Missing numbers
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Weak User",
            "email": "weak@example.com",
            "password": "onlyletters",
            "confirm_password": "onlyletters",
        },
    )
    assert response.status_code == 422


def test_login_success(client: TestClient, test_user_a: User):
    response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"


def test_login_invalid_password_fails_with_generic_message(client: TestClient, test_user_a: User):
    response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_user_fails_with_generic_message(client: TestClient):
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401
    # Generic message prevents user enumeration
    assert "invalid email or password" in response.json()["detail"].lower()


def test_get_current_user_profile(auth_client_a: TestClient, test_user_a: User):
    response = auth_client_a.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user_a.id
    assert data["email"] == test_user_a.email


def test_unauthenticated_request_rejected(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_expired_jwt_rejected(client: TestClient, test_user_a: User):
    # Create expired token
    expired_token = create_access_token(
        data={"sub": str(test_user_a.id)},
        expires_delta=timedelta(minutes=-10),
    )
    client.headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_tampered_jwt_signature_rejected(client: TestClient, user_a_token: str):
    # Tamper token signature
    tampered_token = user_a_token[:-5] + "XXXXX"
    client.headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/auth/me")
    assert response.status_code == 401
