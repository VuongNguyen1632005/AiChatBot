import logging
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings

logger = logging.getLogger(__name__)

# Connection configuration for fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)


class EmailService:
    """
    Dịch vụ gửi email của hệ thống sử dụng fastapi-mail và Gmail SMTP.
    """

    @staticmethod
    async def _send(to: str, subject: str, html_body: str) -> None:
        """
        Hàm gửi email cấp thấp (private helper).
        Đảm bảo wrap trong try/except để không làm crash luồng chính của caller.
        """
        message = MessageSchema(
            subject=subject,
            recipients=[to],
            body=html_body,
            subtype=MessageType.html
        )
        try:
            await fm.send_message(message)
            logger.info(f"✅ Email sent to {to}")
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to}: {str(e)}")

    @staticmethod
    async def send_otp_email(email: str, otp: str) -> None:
        """
        Gửi email chứa OTP cho việc đặt lại mật khẩu.
        """
        subject = "Mã OTP đặt lại mật khẩu - Học Tập Tin Học"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; margin: 0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h2 style="color: #333333; text-align: center; margin-top: 0;">Mã OTP Đặt Lại Mật Khẩu</h2>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">Chào bạn,</p>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">Bạn nhận được email này vì đã yêu cầu đặt lại mật khẩu cho tài khoản của mình. Dưới đây là mã OTP xác thực:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="display: inline-block; font-size: 32px; font-weight: bold; color: #2196F3; letter-spacing: 5px; border: 2px dashed #2196F3; padding: 15px 30px; border-radius: 6px; background-color: #f0f8ff;">
                            {otp}
                        </div>
                    </div>
                    <p style="color: #ff5722; font-size: 14px; font-weight: bold; text-align: center; margin-bottom: 20px;">
                        Mã có hiệu lực trong 5 phút. Không chia sẻ mã này cho bất kỳ ai.
                    </p>
                    <p style="color: #555555; font-size: 14px; line-height: 1.5;">Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
                    <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 30px 0;">
                    <p style="color: #888888; font-size: 12px; text-align: center; margin-bottom: 0;">
                        Học Tập Tin Học
                    </p>
                </div>
            </body>
        </html>
        """
        await EmailService._send(email, subject, html_body)

    @staticmethod
    async def send_verify_email(email: str, token: str) -> None:
        """
        Gửi email chứa liên kết xác thực tài khoản.
        """
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Xác thực tài khoản của bạn - Học Tập Tin Học"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; margin: 0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h2 style="color: #333333; text-align: center; margin-top: 0;">Xác Thực Tài Khoản</h2>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">Chào bạn,</p>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">Cảm ơn bạn đã đăng ký tài khoản trên hệ thống. Vui lòng bấm vào nút bên dưới để hoàn tất xác thực email của bạn:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{link}" style="background-color: #4CAF50; color: #ffffff; padding: 12px 30px; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 5px; display: inline-block;">Xác thực Email</a>
                    </div>
                    <p style="color: #555555; font-size: 14px; text-align: center; margin-bottom: 20px;">
                        Link có hiệu lực trong 24 giờ.
                    </p>
                    <p style="color: #888888; font-size: 14px; line-height: 1.5;">Nếu không phải bạn đăng ký tài khoản này, vui lòng bỏ qua email này.</p>
                    <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 30px 0;">
                    <p style="color: #999999; font-size: 12px;">Nếu nút bấm trên không hiển thị, bạn có thể sao chép và dán liên kết dưới đây vào trình duyệt:<br><a href="{link}" style="color: #4CAF50; word-break: break-all;">{link}</a></p>
                    <p style="color: #888888; font-size: 12px; text-align: center; margin-bottom: 0; margin-top: 20px;">
                        Học Tập Tin Học
                    </p>
                </div>
            </body>
        </html>
        """
        await EmailService.send_verify_email_impl(email, token)

    @classmethod
    async def send_verify_email_impl(cls, email: str, token: str) -> None:
        # Tách logic ra để tránh đệ quy vô hạn khi được gọi (ở trên) và hỗ trợ backward compatibility
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Xác thực tài khoản của bạn - Học Tập Tin Học"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; margin: 0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h2 style="color: #333333; text-align: center; margin-top: 0;">Xác Thực Tài Khoản</h2>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">Chào bạn,</p>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">Cảm ơn bạn đã đăng ký tài khoản trên hệ thống. Vui lòng bấm vào nút bên dưới để hoàn tất xác thực email của bạn:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{link}" style="background-color: #4CAF50; color: #ffffff; padding: 12px 30px; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 5px; display: inline-block;">Xác thực Email</a>
                    </div>
                    <p style="color: #555555; font-size: 14px; text-align: center; margin-bottom: 20px;">
                        Link có hiệu lực trong 24 giờ.
                    </p>
                    <p style="color: #888888; font-size: 14px; line-height: 1.5;">Nếu không phải bạn đăng ký tài khoản này, vui lòng bỏ qua email này.</p>
                    <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 30px 0;">
                    <p style="color: #999999; font-size: 12px;">Nếu nút bấm trên không hiển thị, bạn có thể sao chép và dán liên kết dưới đây vào trình duyệt:<br><a href="{link}" style="color: #4CAF50; word-break: break-all;">{link}</a></p>
                    <p style="color: #888888; font-size: 12px; text-align: center; margin-bottom: 0; margin-top: 20px;">
                        Học Tập Tin Học
                    </p>
                </div>
            </body>
        </html>
        """
        await cls._send(email, subject, html_body)


# Module level aliases for backward compatibility or direct imports
_send = EmailService._send
send_otp_email = EmailService.send_otp_email
send_verify_email = EmailService.send_verify_email_impl
