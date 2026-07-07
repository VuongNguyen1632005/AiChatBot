class OTPInvalidException(Exception):
    status_code = 400
    error_code = "OTP_INVALID"
    message = "Mã OTP không đúng, vui lòng nhập lại"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)

class OTPExpiredException(Exception):
    status_code = 400
    error_code = "OTP_EXPIRED"
    message = "Mã OTP đã hết hạn"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)

class TooManyAttemptsException(Exception):
    status_code = 429
    error_code = "TOO_MANY_ATTEMPTS"
    message = "Bạn đã nhập sai quá số lần cho phép, vui lòng yêu cầu OTP mới"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)

class ResetTokenInvalidException(Exception):
    status_code = 400
    error_code = "RESET_TOKEN_INVALID"
    message = "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)

class VerifyTokenInvalidException(Exception):
    status_code = 400
    error_code = "VERIFY_TOKEN_INVALID"
    message = "Liên kết xác thực không hợp lệ hoặc đã hết hạn"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)

class ResendCooldownException(Exception):
    status_code = 429
    error_code = "RESEND_COOLDOWN"
    message = "Vui lòng đợi 60 giây trước khi yêu cầu gửi lại"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)
class EmailNotVerifiedException(Exception):
    status_code = 403
    error_code = "EMAIL_NOT_VERIFIED"
    message = "Vui lòng xác thực email trước khi đăng nhập"

    def __init__(self, email: str, message: str = None):
        self.email = email
        if message:
            self.message = message
        super().__init__(self.message)


class AccountSuspendedException(Exception):
    status_code = 403
    error_code = "ACCOUNT_SUSPENDED"
    message = "Tài khoản của bạn đã bị khóa, vui lòng liên hệ hỗ trợ"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)


class PhoneAlreadyExistsException(Exception):
    status_code = 400
    error_code = "PHONE_ALREADY_EXISTS"
    message = "Số điện thoại đã được đăng ký"

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(self.message)
