import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_id")
@patch("app.services.auth_service.UserRepository.activate_user")
async def test_verify_email_success(
    mock_activate, mock_get_by_id, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = "1"
    mock_redis.delete = AsyncMock()

    # Mock DB User (Chưa xác thực)
    mock_user = MagicMock()
    mock_user.email_verified = False
    mock_get_by_id.return_value = mock_user

    response = client.get("/api/v1/auth/verify-email?token=valid_token")

    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert data["message"] == "Xác thực email thành công"

    # Kiểm tra gọi các hàm update DB và xóa token
    mock_get_by_id.assert_called_once_with(mock_get_by_id.call_args[0][0], 1)
    mock_activate.assert_called_once_with(mock_activate.call_args[0][0], 1)
    mock_redis.delete.assert_called_once_with("email_verify:valid_token")


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_id")
@patch("app.services.auth_service.UserRepository.activate_user")
async def test_verify_email_idempotent(
    mock_activate, mock_get_by_id, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = "1"
    mock_redis.delete = AsyncMock()

    # Mock DB User (Đã xác thực trước đó)
    mock_user = MagicMock()
    mock_user.email_verified = True
    mock_get_by_id.return_value = mock_user

    response = client.get("/api/v1/auth/verify-email?token=valid_token")

    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert data["message"] == "Email đã được xác thực trước đó"

    # Đã xác thực thì KHÔNG gọi activate hay delete token lần nữa
    mock_activate.assert_not_called()
    mock_redis.delete.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
async def test_verify_email_invalid_token(mock_get_redis):
    # Mock Redis trả về None (không tồn tại/hết hạn)
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = None

    response = client.get("/api/v1/auth/verify-email?token=invalid_token")

    assert response.status_code == 400
    data = response.json()
    assert data["verified"] is False
    assert data["error_code"] == "VERIFY_TOKEN_INVALID"
    assert data["message"] == "Liên kết xác thực không hợp lệ hoặc đã hết hạn"
