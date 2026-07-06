import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_user_by_email")
@patch("app.services.auth_service.UserRepository.create_user")
@patch("app.services.email_service.EmailService.send_verify_email")
async def test_register_verification_success(
    mock_send_email, mock_create_user, mock_get_user, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.setex = AsyncMock()

    # User chưa tồn tại
    mock_get_user.return_value = None

    # Mock User được tạo ra
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.email = "teacher@gmail.com"
    mock_create_user.return_value = mock_user

    response = client.post(
        "/api/v1/auth/register",
        json={
            "fullName": "Nguyen Van A",
            "email": "teacher@gmail.com",
            "phone": "0900000000",
            "gender": "MALE",
            "password": "Password@123",
            "confirmPassword": "Password@123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    # Kiểm tra format response cũ được giữ nguyên
    assert data["success"] is True
    assert data["data"]["userId"] == 123
    assert data["data"]["email"] == "teacher@gmail.com"
    assert data["data"]["verifyRequired"] is True

    # Kiểm tra đã lưu token vào Redis và gửi mail
    mock_redis.setex.assert_called_once()
    mock_send_email.assert_called_once_with("teacher@gmail.com", mock_send_email.call_args[0][1])


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_user_by_email")
@patch("app.services.auth_service.UserRepository.create_user")
@patch("app.services.email_service.EmailService.send_verify_email")
async def test_register_verification_email_error_graceful(
    mock_send_email, mock_create_user, mock_get_user, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis

    # Email gửi lỗi (ví dụ quăng exception)
    mock_send_email.side_effect = Exception("SMTP Connection Timeout")

    mock_get_user.return_value = None

    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.email = "teacher@gmail.com"
    mock_create_user.return_value = mock_user

    response = client.post(
        "/api/v1/auth/register",
        json={
            "fullName": "Nguyen Van A",
            "email": "teacher@gmail.com",
            "phone": "0900000000",
            "gender": "MALE",
            "password": "Password@123",
            "confirmPassword": "Password@123"
        }
    )

    # API Register vẫn PHẢI trả về 201 tạo tài khoản thành công
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["userId"] == 123
    assert data["data"]["email"] == "teacher@gmail.com"
    assert data["data"]["verifyRequired"] is True
