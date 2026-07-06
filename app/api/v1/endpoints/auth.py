from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgresql.session import get_db
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.schemas.auth import (
    RegisterRequest, RegisterResponseData, LoginRequest, LoginResponseData,
    ForgotPasswordRequest, ForgotPasswordResponse, VerifyOTPRequest, VerifyOTPResponse, VerifyOTPErrorResponse,
    ResetPasswordRequest, ResetPasswordResponse, ResetPasswordErrorResponse, VerifyEmailResponse,
    ResendVerificationRequest, ResendVerificationResponse
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from app.core.exceptions import OTPInvalidException, OTPExpiredException, TooManyAttemptsException, ResetTokenInvalidException, VerifyTokenInvalidException, ResendCooldownException

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

@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": VerifyOTPErrorResponse, "description": "OTP không chính xác hoặc đã hết hạn"},
        429: {"model": VerifyOTPErrorResponse, "description": "Quá số lần thử cho phép"}
    },
    summary="Xác thực mã OTP quên mật khẩu"
)
async def verify_otp(request: VerifyOTPRequest):
    """
    Xác thực OTP được gửi trong luồng quên mật khẩu.
    Nếu OTP chính xác, trả về một resetToken có thời hạn 10 phút.
    """
    try:
        response = await AuthService.verify_otp(request.email, request.otp)
        return response
    except (OTPInvalidException, OTPExpiredException, TooManyAttemptsException) as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "verified": False,
                "error_code": e.error_code,
                "message": e.message
            }
        )

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ResetPasswordErrorResponse, "description": "Token không hợp lệ hoặc hết hạn"},
        422: {"model": ResetPasswordErrorResponse, "description": "Mật khẩu không khớp hoặc quá yếu"}
    },
    summary="Đặt lại mật khẩu mới"
)
async def reset_password(
    request_data: dict = Body(..., example={
        "resetToken": "reset_token_here",
        "newPassword": "Password@123",
        "confirmPassword": "Password@123"
    }),
    db: AsyncSession = Depends(get_db)
):
    """
    Đặt lại mật khẩu mới sau khi xác thực thành công mã OTP ở bước trước.
    """
    # 1. Validate bằng Pydantic Schema thủ công để trả về đúng cấu trúc mã lỗi yêu cầu
    try:
        request = ResetPasswordRequest(**request_data)
    except ValidationError as e:
        for error in e.errors():
            msg = error.get("msg")
            # Làm sạch thông báo lỗi của Pydantic custom validators
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            
            # Phân loại mã lỗi
            error_code = "PASSWORD_MISMATCH" if "không khớp" in msg else "PASSWORD_TOO_WEAK"
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "resetSuccess": False,
                    "error_code": error_code,
                    "message": msg
                }
            )

    # 2. Gọi dịch vụ thực hiện logic đặt lại mật khẩu
    try:
        response = await AuthService.reset_password(db, request.resetToken, request.newPassword)
        return response
    except ResetTokenInvalidException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "resetSuccess": False,
                "error_code": e.error_code,
                "message": e.message
            }
        )

@router.get(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": VerifyEmailResponse, "description": "Token xác thực không hợp lệ hoặc đã hết hạn"}
    },
    summary="Xác thực email đăng ký tài khoản"
)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Xác thực email người dùng thông qua mã token được gửi qua email.
    """
    try:
        response = await AuthService.verify_email(db, token)
        return response
    except VerifyTokenInvalidException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "verified": False,
                "error_code": e.error_code,
                "message": e.message
            }
        )

@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        429: {"model": ResendVerificationResponse, "description": "Gửi lại quá nhanh, đang trong thời gian cooldown"}
    },
    summary="Gửi lại liên kết xác thực email"
)
async def resend_verification(request: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    """
    Gửi lại email xác minh tài khoản nếu liên kết trước đó bị hết hạn hoặc thất lạc.
    Áp dụng cooldown 60 giây chống spam.
    """
    try:
        response = await AuthService.resend_verification(db, request.email)
        return response
    except ResendCooldownException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "resent": False,
                "error_code": e.error_code,
                "message": e.message
            }
        )
