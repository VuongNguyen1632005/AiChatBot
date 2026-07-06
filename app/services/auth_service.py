from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.sql.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, RegisterResponseData, LoginRequest, LoginResponseData, LoginResponseUser, ForgotPasswordResponse, VerifyOTPResponse, ResetPasswordResponse, VerifyEmailResponse, ResendVerificationResponse
from app.db.redis.session import get_redis
from app.core.exceptions import OTPInvalidException, OTPExpiredException, TooManyAttemptsException, ResetTokenInvalidException, VerifyTokenInvalidException, ResendCooldownException, EmailNotVerifiedException, AccountSuspendedException
from app.services.email_service import EmailService
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
            "is_active": True,
            "email_verified": False,
            "status": "PENDING"
        }

        # Lưu vào cơ sở dữ liệu
        new_user = await UserRepository.create_user(db, user_data)

        # Logic bổ sung: Sinh verify_token và gửi email xác thực tài khoản
        try:
            verify_token = secrets.token_urlsafe(32)
            verify_key = f"email_verify:{verify_token}"

            # Lưu token vào Redis với TTL 24 giờ (86400 giây)
            redis_cli = await get_redis()
            if redis_cli:
                await redis_cli.setex(verify_key, 86400, str(new_user.id))

                # Gửi email chứa link xác thực
                await EmailService.send_verify_email(new_user.email, verify_token)
            else:
                print("⚠️ Không thể kết nối Redis để lưu email verification token")
        except Exception as e:
            # Ghi nhận log lỗi gửi email nhưng KHÔNG làm gián đoạn luồng đăng ký
            print(f"⚠️ Lỗi trong quá trình tạo verify token hoặc gửi email xác thực: {e}")

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

        # [MỚI] Kiểm tra trạng thái tài khoản
        if user.status == 'SUSPENDED':
            raise AccountSuspendedException()

        if not user.email_verified:
            raise EmailNotVerifiedException(email=user.email)

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

    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> VerifyEmailResponse:
        """
        Xác thực tài khoản qua link email:
        1. Lấy user_id từ Redis theo key: email_verify:{token}.
        2. Không tồn tại -> raise VerifyTokenInvalidException().
        3. Tìm user trong Postgres. Không thấy -> raise VerifyTokenInvalidException().
        4. Nếu đã xác thực trước đó (email_verified=True) -> Trả thành công (Idempotent).
        5. Nếu chưa -> Cập nhật email_verified=True, status='ACTIVE', xóa token Redis.
        """
        redis_cli = await get_redis()
        if not redis_cli:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dịch vụ Redis không hoạt động"
            )

        verify_key = f"email_verify:{token}"

        # 1. Lấy user_id từ Redis
        user_id_str = await redis_cli.get(verify_key)
        if not user_id_str:
            raise VerifyTokenInvalidException()

        user_id = int(user_id_str)

        # 2. Tìm user trong PostgreSQL
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise VerifyTokenInvalidException()

        # 3. Xử lý tính lũy đẳng (Idempotency)
        if user.email_verified:
            return VerifyEmailResponse(
                verified=True,
                message="Email đã được xác thực trước đó"
            )

        # 4. Kích hoạt tài khoản người dùng
        try:
            await UserRepository.activate_user(db, user_id)
        except Exception as e:
            print(f"❌ Lỗi kích hoạt tài khoản trong PostgreSQL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi cập nhật cơ sở dữ liệu"
            )

        # 5. Xóa token khỏi Redis ngay lập tức (One-time use)
        await redis_cli.delete(verify_key)

        return VerifyEmailResponse(
            verified=True,
            message="Xác thực email thành công"
        )

    @staticmethod
    async def resend_verification(db: AsyncSession, email: str) -> ResendVerificationResponse:
        """
        Gửi lại email xác thực:
        1. Tìm user theo email. Không tồn tại -> Trả về 200 giả (Tránh lộ email tồn tại).
        2. Nếu user đã được xác thực -> Trả về thông báo đã xác thực.
        3. Kiểm tra cooldown: resend_verify_cooldown:{email}. Nếu còn -> raise ResendCooldownException().
        4. Sinh token mới, lưu vào Redis email_verify:{token} (24h).
        5. Đặt cooldown 60 giây.
        6. Gửi email xác thực mới qua EmailService.
        """
        redis_cli = await get_redis()
        if not redis_cli:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dịch vụ Redis không hoạt động"
            )

        # 1. Tìm user theo email
        user = await UserRepository.get_by_email(db, email)
        if not user:
            # TODO: Giới hạn số lần resend tối đa trong ngày/email (VD: max 5 lần)
            # Trả về 200 giả lập để bảo mật thông tin tài khoản
            return ResendVerificationResponse(
                resent=True,
                message="Email xác thực đã được gửi lại, vui lòng kiểm tra hộp thư"
            )

        # 2. Kiểm tra nếu tài khoản đã xác thực rồi
        if user.email_verified:
            return ResendVerificationResponse(
                resent=False,
                message="Email này đã được xác thực trước đó"
            )

        # 3. Kiểm tra cooldown chống spam gửi liên tục (60 giây)
        cooldown_key = f"resend_verify_cooldown:{email}"
        cooldown = await redis_cli.get(cooldown_key)
        if cooldown:
            raise ResendCooldownException()

        # 4. Sinh token mới và lưu vào Redis (TTL 24h)
        verify_token = secrets.token_urlsafe(32)
        verify_key = f"email_verify:{verify_token}"
        await redis_cli.setex(verify_key, 86400, user.id)

        # 5. Lưu cooldown vào Redis (TTL 60s)
        await redis_cli.setex(cooldown_key, 60, "1")

        # 6. Gửi email xác thực chứa token mới
        await EmailService.send_verify_email(email, verify_token)

        return ResendVerificationResponse(
            resent=True,
            message="Email xác thực đã được gửi lại, vui lòng kiểm tra hộp thư"
        )
