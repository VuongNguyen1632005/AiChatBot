import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_email")
@patch("app.services.email_service.EmailService.send_verify_email")
async def test_resend_verification_success(
    mock_send_email, mock_get_by_email, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = None  # No cooldown
    mock_redis.setex = AsyncMock()

    # Mock DB User
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email_verified = False
    mock_get_by_email.return_value = mock_user

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "teacher@gmail.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resent"] is True
    assert "gửi lại" in data["message"]

    # Kiểm tra việc sinh token, set cooldown và gửi mail
    assert mock_redis.setex.call_count == 2
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_email")
@patch("app.services.email_service.EmailService.send_verify_email")
async def test_resend_verification_nonexistent_user(
    mock_send_email, mock_get_by_email, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = None
    mock_redis.setex = AsyncMock()

    # Mock DB User không tồn tại
    mock_get_by_email.return_value = None

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "notfound@gmail.com"}
    )

    # Vẫn trả về 200 và thông báo như thật để tránh user enumeration
    assert response.status_code == 200
    data = response.json()
    assert data["resent"] is True
    assert "gửi lại" in data["message"]

    # Không gửi mail và không lưu token
    mock_redis.setex.assert_not_called()
    mock_send_email.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_email")
@patch("app.services.email_service.EmailService.send_verify_email")
async def test_resend_verification_already_verified(
    mock_send_email, mock_get_by_email, mock_get_redis
):
    # Mock Redis
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = None

    # Mock DB User đã xác thực rồi
    mock_user = MagicMock()
    mock_user.email_verified = True
    mock_get_by_email.return_value = mock_user

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "verified@gmail.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resent"] is False
    assert data["message"] == "Email này đã được xác thực trước đó"

    # Không gửi mail và không lưu token
    mock_redis.setex.assert_not_called()
    mock_send_email.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
@patch("app.services.auth_service.UserRepository.get_by_email")
async def test_resend_verification_cooldown(mock_get_by_email, mock_get_redis):
    # Mock Redis trả về cooldown còn hiệu lực
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = "1"

    # Mock DB User
    mock_user = MagicMock()
    mock_user.email_verified = False
    mock_get_by_email.return_value = mock_user

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "teacher@gmail.com"}
    )

    assert response.status_code == 429
    data = response.json()
    assert data["resent"] is False
    assert data["error_code"] == "RESEND_COOLDOWN"
    assert data["message"] == "Vui lòng đợi 60 giây trước khi yêu cầu gửi lại"
