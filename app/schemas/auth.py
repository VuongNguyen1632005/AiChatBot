from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from typing import Optional

class RegisterRequest(BaseModel):
    """
    Schema yêu cầu đăng ký người dùng mới.
    """
    fullName: str = Field(..., min_length=1, description="Họ và tên của người dùng")
    email: EmailStr = Field(..., description="Email đăng ký tài khoản")
    phone: Optional[str] = Field(None, description="Số điện thoại")
    gender: Optional[str] = Field(None, description="Giới tính")
    password: str = Field(..., min_length=6, description="Mật khẩu (tối thiểu 6 ký tự)")
    confirmPassword: str = Field(..., min_length=6, description="Mật khẩu xác nhận lại")

    @field_validator("confirmPassword")
    @classmethod
    def verify_passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return v

class RegisterResponseData(BaseModel):
    """
    Dữ liệu trả về khi đăng ký thành công.
    """
    userId: int = Field(..., description="ID của người dùng mới")
    email: EmailStr = Field(..., description="Email của người dùng mới")
    verifyRequired: bool = Field(True, description="Yêu cầu kích hoạt/xác thực email")

class LoginRequest(BaseModel):
    """
    Schema yêu cầu đăng nhập.
    """
    email: EmailStr = Field(..., description="Email đăng nhập")
    password: str = Field(..., min_length=6, description="Mật khẩu tài khoản")

class LoginResponseUser(BaseModel):
    """
    Thông tin người dùng trả về trong phiên đăng nhập.
    """
    id: int = Field(..., description="ID người dùng")
    fullName: str = Field(..., description="Họ tên người dùng")
    email: EmailStr = Field(..., description="Email người dùng")
    role: str = Field(..., description="Vai trò của người dùng trong hệ thống (ví dụ: TEACHER)")

class LoginResponseData(BaseModel):
    """
    Dữ liệu trả về khi đăng nhập thành công bao gồm Tokens.
    """
    accessToken: str = Field(..., description="Access Token (JWT)")
    refreshToken: str = Field(..., description="Refresh Token (JWT)")
    user: LoginResponseUser = Field(..., description="Thông tin người dùng")
