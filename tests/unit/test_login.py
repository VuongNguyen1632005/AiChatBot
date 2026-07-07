import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.services.auth_service.UserRepository.get_user_by_email")
@patch("app.services.auth_service.verify_password")
async def test_login_suspended_account(mock_verify_password, mock_get_user):
    # Mock user exists with password matched but status is SUSPENDED
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.email = "suspended@gmail.com"
    mock_user.password_hash = "hashed_password"
    mock_user.is_active = True
    mock_user.status = "SUSPENDED"
    mock_user.email_verified = True
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = True

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "suspended@gmail.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == "ACCOUNT_SUSPENDED"
    assert data["message"] == "Tài khoản của bạn đã bị khóa, vui lòng liên hệ hỗ trợ"


@pytest.mark.asyncio
@patch("app.services.auth_service.UserRepository.get_user_by_email")
@patch("app.services.auth_service.verify_password")
async def test_login_email_not_verified(mock_verify_password, mock_get_user):
    # Mock user exists with password matched, status PENDING, and email_verified=False
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.email = "unverified@gmail.com"
    mock_user.password_hash = "hashed_password"
    mock_user.is_active = True
    mock_user.status = "PENDING"
    mock_user.email_verified = False
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = True

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unverified@gmail.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == "EMAIL_NOT_VERIFIED"
    assert data["message"] == "Vui lòng xác thực email trước khi đăng nhập"
    assert data["email"] == "unverified@gmail.com"
