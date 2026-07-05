from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgresql.session import get_db
from app.schemas.auth import RegisterRequest, RegisterResponseData, LoginRequest, LoginResponseData, ForgotPasswordRequest, ForgotPasswordResponse
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post(
    "/register",
    response_model=ApiResponse[RegisterResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới"
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Đăng ký tài khoản giáo viên mới trên hệ thống ETECHS.
    Các trường thông tin bắt buộc gồm email, fullName, password, confirmPassword.
    """
    data = await AuthService.register(db, request)
    return ApiResponse(
        success=True,
        message="Thao tác thành công",
        data=data,
        errors=None
    )

@router.post(
    "/login",
    response_model=ApiResponse[LoginResponseData],
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập hệ thống"
)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Đăng nhập bằng Email và Mật khẩu để nhận JWT Access Token và Refresh Token.
    """
    data = await AuthService.login(db, request)
    return ApiResponse(
        success=True,
        message="Thao tác thành công",
        data=data,
        errors=None
    )

@router.post(
    "/forgot-password",
    response_model=ApiResponse[ForgotPasswordResponse],
    status_code=status.HTTP_200_OK,
    summary="Yêu cầu khôi phục mật khẩu (Gửi OTP)"
)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Yêu cầu khôi phục mật khẩu qua Email.
    Gửi mã OTP 6 số đến email của người dùng (nếu tồn tại) và lưu trữ trong Redis/MongoDB trong 300 giây.
    
    *Gợi ý tích hợp SlowAPI để Rate Limit:*
    Để giới hạn 3 request/phút/IP, bạn có thể cấu hình SlowAPI như sau:
    @limiter.limit("3/minute")
    async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
        ...
    """
    data = await AuthService.forgot_password(db, request.email)
    return ApiResponse(
        success=True,
        message="Thao tác thành công",
        data=data,
        errors=None
    )
