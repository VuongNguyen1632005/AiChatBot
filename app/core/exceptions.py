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
