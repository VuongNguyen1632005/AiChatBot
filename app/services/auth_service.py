from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.sql.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, RegisterResponseData, LoginRequest, LoginResponseData, LoginResponseUser, ForgotPasswordResponse
from app.db.redis.session import get_redis
from app.db.mongodb.session import db_mongo
from app.utils.email_sender import send_otp_email
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
