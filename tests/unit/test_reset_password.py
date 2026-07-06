import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_email")
@patch("app.services.auth_service.UserRepository.update_password")
@patch("app.services.auth_service.send_password_changed_email")
async def test_reset_password_success(
    mock_send_email, mock_update_password, mock_get_user, mock_get_redis
):
    # Mock Redis client
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = "teacher@gmail.com"
    mock_redis.delete = AsyncMock()

    # Mock DB User
    mock_user = MagicMock()
    mock_get_user.return_value = mock_user

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "resetToken": "token_123",
            "newPassword": "Password@123",
            "confirmPassword": "Password@123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resetSuccess"] is True

    # Kiểm tra các hàm nghiệp vụ được gọi đúng
    mock_redis.get.assert_called_once_with("reset_token:token_123")
    mock_redis.delete.assert_called_once_with("reset_token:token_123")
    mock_get_user.assert_called_once()
    mock_update_password.assert_called_once()
    mock_send_email.assert_called_once_with("teacher@gmail.com")


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
async def test_reset_password_invalid_token(mock_get_redis):
    # Mock Redis trả về None (hết hạn hoặc không tồn tại)
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = None

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "resetToken": "token_invalid",
            "newPassword": "Password@123",
            "confirmPassword": "Password@123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["resetSuccess"] is False
    assert data["error_code"] == "RESET_TOKEN_INVALID"
    assert data["message"] == "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn"


@pytest.mark.asyncio
async def test_reset_password_mismatch():
    # Passwords không khớp
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "resetToken": "token_123",
            "newPassword": "Password@123",
            "confirmPassword": "Password@1234"
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["resetSuccess"] is False
    assert data["error_code"] == "PASSWORD_MISMATCH"
    assert data["message"] == "Mật khẩu xác nhận không khớp"


@pytest.mark.asyncio
async def test_reset_password_too_weak_length():
    # Độ dài ngắn hơn 8 ký tự
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "resetToken": "token_123",
            "newPassword": "Pwd@1",
            "confirmPassword": "Pwd@1"
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["resetSuccess"] is False
    assert data["error_code"] == "PASSWORD_TOO_WEAK"
    assert "ít nhất 8 ký tự" in data["message"]


@pytest.mark.asyncio
async def test_reset_password_too_weak_no_upper():
    # Không có chữ hoa
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "resetToken": "token_123",
            "newPassword": "password@123",
            "confirmPassword": "password@123"
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["resetSuccess"] is False
    assert data["error_code"] == "PASSWORD_TOO_WEAK"
    assert "chữ hoa" in data["message"]
