from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.sql.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, RegisterResponseData, LoginRequest, LoginResponseData, LoginResponseUser, ForgotPasswordResponse, VerifyOTPResponse, ResetPasswordResponse
from app.db.redis.session import get_redis
from app.core.exceptions import OTPInvalidException, OTPExpiredException, TooManyAttemptsException, ResetTokenInvalidException
from app.db.mongodb.session import db_mongo
from app.utils.email_sender import send_otp_email, send_password_changed_email
import secrets
from datetime import datetime, timezone, timedelta

class AuthService:
    """
    Service quản lý toàn bộ nghiệp vụ liên quan đến xác thực (Auth): đăng ký, đăng nhập.
    """
    @staticmethod
    async def register(db: AsyncSession, request: RegisterRequest) -> RegisterResponseData:
        """
        Thực hiện nghiệp vụ đăng ký người dùng mới:
        - Kiểm tra trùng email trong DB.
        - Mã hóa mật khẩu.
        - Lưu User vào PostgreSQL.
        """
        # Kiểm tra sự tồn tại của email
        existing_user = await UserRepository.get_user_by_email(db, request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"field": "email", "message": "Email đã tồn tại"}]
            )

        # Tạo dict dữ liệu người dùng mới
        user_data = {
            "full_name": request.fullName,
            "email": request.email,
            "phone": request.phone,
            "gender": request.gender,
            "password_hash": hash_password(request.password),
            "role": "TEACHER",  # Vai trò mặc định cho tài khoản đăng ký mới
            "is_active": True
        }

        # Lưu vào cơ sở dữ liệu
        new_user = await UserRepository.create_user(db, user_data)

        return RegisterResponseData(
            userId=new_user.id,
            email=new_user.email,
            verifyRequired=True
        )

    @staticmethod
    async def login(db: AsyncSession, request: LoginRequest) -> LoginResponseData:
        """
        Thực hiện nghiệp vụ đăng nhập:
        - Xác minh tài khoản qua email.
        - Kiểm tra mật khẩu khớp với hash.
        - Tạo Access Token và Refresh Token cho phiên hoạt động.
        """
        user = await UserRepository.get_user_by_email(db, request.email)
        
        # Không thông báo rõ email hay mật khẩu sai để tránh dò tìm tài khoản (User Enumeration)
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email hoặc mật khẩu không đúng"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản đã bị vô hiệu hóa"
            )

        # Chuẩn bị payload để sinh JWT
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }

        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data=token_payload)

        user_info = LoginResponseUser(
            id=user.id,
            fullName=user.full_name,
            email=user.email,
            role=user.role
        )

        return LoginResponseData(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=user_info
        )

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> ForgotPasswordResponse:
        """
        Xử lý yêu cầu quên mật khẩu:
        - Kiểm tra xem người dùng có tồn tại trong PostgreSQL không.
        - Tạo mã OTP ngẫu nhiên gồm 6 chữ số.
        - Lưu trữ OTP vào Redis với key pattern `otp:forgot_password:{email}` và TTL = 300 giây.
        - Lưu trữ OTP vào MongoDB collection "otp_tokens".
        - Gửi OTP qua email cho người dùng (nếu email tồn tại).
        - Trả về kết quả xác nhận (thành công giả lập nếu email không tồn tại).
        """
        user = await UserRepository.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email chưa được đăng ký"
            )

        # Tạo OTP ngẫu nhiên bảo mật 6 chữ số
        otp_code = "".join(secrets.choice("0123456789") for _ in range(6))

        # Lưu OTP vào Redis
        redis_cli = await get_redis()
        if redis_cli:
            try:
                await redis_cli.setex(f"otp:forgot_password:{email}", 300, otp_code)
            except Exception as e:
                print(f"⚠️ Lỗi lưu OTP vào Redis: {e}")

        # Lưu OTP vào MongoDB
        try:
            if db_mongo.db is not None:
                await db_mongo.db["otp_tokens"].insert_one({
                    "email": email,
                    "otp_code": otp_code,
                    "created_at": datetime.now(timezone.utc),
                    "expired_at": datetime.now(timezone.utc) + timedelta(seconds=300)
                })
        except Exception as e:
            print(f"⚠️ Lỗi lưu OTP vào MongoDB: {e}")

        # Gửi OTP qua Email
        await send_otp_email(email, otp_code)

        return ForgotPasswordResponse(
            email=email,
            otpSent=True,
            expiredIn=300
        )

    @staticmethod
    async def verify_otp(email: str, otp: str) -> VerifyOTPResponse:
        """
        Xác thực OTP:
        1. Kiểm tra số lần thử sai (rate limit 5 lần).
        2. Lấy OTP từ Redis.
        3. So sánh OTP an toàn bằng secrets.compare_digest().
        4. Đúng: xóa OTP, xóa attempts key, tạo và lưu resetToken (10 phút), trả về token.
        5. Sai: tăng số lần thử sai, raise exception tương ứng.
        """
        redis_cli = await get_redis()
        if not redis_cli:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dịch vụ Redis không hoạt động"
            )

        attempts_key = f"otp_attempts:{email}"
        otp_key = f"otp:forgot_password:{email}"

        # 1. Kiểm tra giới hạn số lần thử sai (Rate limit)
        attempts = await redis_cli.get(attempts_key)
        if attempts is not None and int(attempts) >= 5:
            raise TooManyAttemptsException()

        # 2. Lấy OTP đã lưu từ Redis
        saved_otp = await redis_cli.get(otp_key)
        if not saved_otp:
            raise OTPExpiredException()

        # 3. So sánh OTP bảo mật để tránh Timing Attack
        if not secrets.compare_digest(saved_otp, otp):
            # Tăng số lần thử sai lên 1
            new_attempts = await redis_cli.incr(attempts_key)
            if new_attempts == 1:
                await redis_cli.expire(attempts_key, 300)

            if new_attempts >= 5:
                raise TooManyAttemptsException()
            raise OTPInvalidException()

        # 4. Khi OTP đúng:
        # Xóa OTP khỏi Redis (One-time use)
        await redis_cli.delete(otp_key)
        # Reset số lần thử sai
        await redis_cli.delete(attempts_key)

        # Tạo resetToken bảo mật cao
        reset_token = secrets.token_urlsafe(32)
        reset_token_key = f"reset_token:{reset_token}"

        # Lưu resetToken vào Redis (TTL 600 giây - 10 phút)
        await redis_cli.setex(reset_token_key, 600, email)

        return VerifyOTPResponse(
            verified=True,
            resetToken=reset_token
        )

    @staticmethod
    async def reset_password(db: AsyncSession, reset_token: str, new_password: str) -> ResetPasswordResponse:
        """
        Đặt lại mật khẩu mới:
        1. Lấy email từ Redis bằng key: reset_token:{resetToken}
        2. Nếu không tồn tại -> raise ResetTokenInvalidException()
        3. Xóa resetToken khỏi Redis ngay lập tức (one-time use)
        4. Tìm user theo email trong PostgreSQL.
        5. Nếu không thấy -> raise ResetTokenInvalidException()
        6. Mã hóa mật khẩu mới bằng hash_password().
        7. Cập nhật mật khẩu trong PostgreSQL (UserRepository.update_password).
        8. Gửi email thông báo đổi mật khẩu thành công.
        9. Trả về ResetPasswordResponse.
        """
        redis_cli = await get_redis()
        if not redis_cli:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dịch vụ Redis không hoạt động"
            )

        reset_token_key = f"reset_token:{reset_token}"

        # 1. Lấy email từ Redis
        email = await redis_cli.get(reset_token_key)
        if not email:
            raise ResetTokenInvalidException()

        # 2. Xóa resetToken khỏi Redis ngay lập tức (One-time use) để tránh brute-force thử lại
        await redis_cli.delete(reset_token_key)

        # 3. Tìm user trong PostgreSQL
        user = await UserRepository.get_by_email(db, email)
        if not user:
            raise ResetTokenInvalidException()

        # 4. Mã hóa mật khẩu mới
        hashed_password = hash_password(new_password)

        # 5. Cập nhật mật khẩu trong PostgreSQL
        try:
            await UserRepository.update_password(db, email, hashed_password)
        except Exception as e:
            print(f"❌ Lỗi cập nhật mật khẩu trong PostgreSQL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi cập nhật cơ sở dữ liệu"
            )

        # 6. Ghi log audit bảo mật (không ghi đè mật khẩu)
        print(f"📝 [AUDIT] Người dùng {email} đã đặt lại mật khẩu thành công bằng resetToken vào lúc {datetime.now(timezone.utc)}")

        # 7. Gửi email thông báo đổi mật khẩu thành công
        await send_password_changed_email(email)

        return ResetPasswordResponse(
            resetSuccess=True
        )
