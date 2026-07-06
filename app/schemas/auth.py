from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo, model_validator
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

class ForgotPasswordRequest(BaseModel):
    """
    Schema yêu cầu đặt lại mật khẩu.
    """
    email: EmailStr = Field(..., description="Email của tài khoản cần lấy lại mật khẩu")

class ForgotPasswordResponse(BaseModel):
    """
    Dữ liệu trả về sau khi gửi OTP đặt lại mật khẩu thành công.
    """
    email: EmailStr = Field(..., description="Email nhận mã OTP")
    otpSent: bool = Field(..., description="Trạng thái đã gửi OTP")
    expiredIn: int = Field(..., description="Thời gian hết hạn của OTP tính bằng giây (ví dụ: 300)")

class VerifyOTPRequest(BaseModel):
    """
    Schema yêu cầu xác thực OTP.
    """
    email: EmailStr = Field(..., description="Email của tài khoản cần xác thực OTP")
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Mã OTP gồm 6 chữ số"
    )

class VerifyOTPResponse(BaseModel):
    """
    Dữ liệu trả về khi xác thực OTP thành công.
    """
    verified: bool = Field(..., description="Trạng thái xác thực thành công")
    resetToken: Optional[str] = Field(None, description="Token dùng để đặt lại mật khẩu")

class VerifyOTPErrorResponse(BaseModel):
    """
    Dữ liệu trả về khi xác thực OTP thất bại.
    """
    verified: bool = Field(False, description="Trạng thái xác thực thất bại")
    error_code: str = Field(..., description="Mã lỗi xác thực")
    message: str = Field(..., description="Thông điệp chi tiết lỗi")

class ResetPasswordRequest(BaseModel):
    """
    Schema yêu cầu đặt lại mật khẩu mới.
    """
    resetToken: str = Field(..., description="Token xác thực để đặt lại mật khẩu")
    newPassword: str = Field(..., description="Mật khẩu mới")
    confirmPassword: str = Field(..., description="Xác nhận mật khẩu mới")

    @model_validator(mode="after")
    def validate_password_and_match(self) -> 'ResetPasswordRequest':
        # 1. Kiểm tra độ dài tối thiểu 8 ký tự
        if len(self.newPassword) < 8:
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
            
        # 2. Kiểm tra độ mạnh mật khẩu (1 chữ hoa, 1 chữ thường, 1 số)
        if not any(c.isupper() for c in self.newPassword):
            raise ValueError("Mật khẩu phải có ít nhất 1 chữ hoa, 1 chữ thường và 1 chữ số")
        if not any(c.islower() for c in self.newPassword):
            raise ValueError("Mật khẩu phải có ít nhất 1 chữ hoa, 1 chữ thường và 1 chữ số")
        if not any(c.isdigit() for c in self.newPassword):
            raise ValueError("Mật khẩu phải có ít nhất 1 chữ hoa, 1 chữ thường và 1 chữ số")
            
        # 3. Kiểm tra trùng khớp mật khẩu xác nhận
        if self.newPassword != self.confirmPassword:
            raise ValueError("Mật khẩu xác nhận không khớp")
            
        return self

class ResetPasswordResponse(BaseModel):
    """
    Dữ liệu trả về khi đặt lại mật khẩu thành công.
    """
    resetSuccess: bool = Field(True, description="Trạng thái đặt lại mật khẩu thành công")

class ResetPasswordErrorResponse(BaseModel):
    """
    Dữ liệu trả về khi đặt lại mật khẩu thất bại.
    """
    resetSuccess: bool = Field(False, description="Trạng thái đặt lại mật khẩu thất bại")
    error_code: str = Field(..., description="Mã lỗi hệ thống")
    message: str = Field(..., description="Thông điệp lỗi chi tiết")

class VerifyEmailResponse(BaseModel):
    """
    Dữ liệu trả về khi xác thực email.
    """
    verified: bool = Field(..., description="Trạng thái xác thực email thành công hay thất bại")
    message: str = Field(..., description="Thông báo kết quả chi tiết")
