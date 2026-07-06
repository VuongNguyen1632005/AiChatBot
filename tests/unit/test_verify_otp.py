import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
async def test_verify_otp_success(mock_get_redis):
    # Mock Redis client
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # Mock Redis get responses
    # Lần 1 (lấy số lần thử): None
    # Lần 2 (lấy OTP): "123456"
    mock_redis.get.side_effect = [None, "123456"]
    mock_redis.delete = AsyncMock()
    mock_redis.setex = AsyncMock()
    
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "teacher@gmail.com", "otp": "123456"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert "resetToken" in data
    assert data["resetToken"] is not None
    
    # Kiểm tra các hàm xóa OTP và lưu resetToken được gọi
    mock_redis.delete.assert_any_call("otp:forgot_password:teacher@gmail.com")
    mock_redis.delete.assert_any_call("otp_attempts:teacher@gmail.com")
    mock_redis.setex.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
async def test_verify_otp_invalid(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # Lần 1 (lấy số lần thử): None
    # Lần 2 (lấy OTP): "123456"
    mock_redis.get.side_effect = [None, "123456"]
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock()
    
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "teacher@gmail.com", "otp": "111111"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["verified"] is False
    assert data["error_code"] == "OTP_INVALID"
    assert data["message"] == "Mã OTP không đúng, vui lòng nhập lại"
    
    mock_redis.incr.assert_called_once_with("otp_attempts:teacher@gmail.com")
    mock_redis.expire.assert_called_once_with("otp_attempts:teacher@gmail.com", 300)

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
async def test_verify_otp_expired(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # Lần 1 (lấy số lần thử): None
    # Lần 2 (lấy OTP): None (hết hạn)
    mock_redis.get.side_effect = [None, None]
    
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "teacher@gmail.com", "otp": "123456"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["verified"] is False
    assert data["error_code"] == "OTP_EXPIRED"
    assert data["message"] == "Mã OTP đã hết hạn"

@pytest.mark.asyncio
@patch("app.services.auth_service.get_redis")
async def test_verify_otp_too_many_attempts(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # Lần 1 (lấy số lần thử): "5" (đã sai quá 5 lần và bị khóa)
    mock_redis.get.side_effect = ["5"]
    
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "teacher@gmail.com", "otp": "123456"}
    )
    
    assert response.status_code == 429
    data = response.json()
    assert data["verified"] is False
    assert data["error_code"] == "TOO_MANY_ATTEMPTS"
    assert data["message"] == "Bạn đã nhập sai quá số lần cho phép, vui lòng yêu cầu OTP mới"
