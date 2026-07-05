from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgresql.session import get_db
from app.schemas.auth import RegisterRequest, RegisterResponseData, LoginRequest, LoginResponseData
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
