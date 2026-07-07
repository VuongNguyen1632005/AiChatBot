from app.services.email_service import EmailService

async def send_otp_email(email: str, otp: str) -> None:
    """
    Chuyển tiếp việc gửi OTP email sang EmailService sử dụng fastapi-mail.
    """
    await EmailService.send_otp_email(email, otp)


async def send_password_changed_email(email: str) -> None:
    """
    Gửi email thông báo đổi mật khẩu thành công qua EmailService.
    """
    subject = "Thông báo: Mật khẩu của bạn đã được thay đổi - Học Tập Tin Học"
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h2 style="color: #333333; text-align: center; margin-top: 0;">Thay Đổi Mật Khẩu Thành Công</h2>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Chào bạn,</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Mật khẩu cho tài khoản <strong>{email}</strong> của bạn vừa được thay đổi thành công.</p>
                <p style="color: #ff5722; font-size: 14px; font-weight: bold; margin-bottom: 20px;">
                    ⚠️ Nếu không phải bạn thực hiện thay đổi này, vui lòng liên hệ ngay với chúng tôi để bảo vệ tài khoản.
                </p>
                <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 30px 0;">
                <p style="color: #888888; font-size: 12px; text-align: center; margin-bottom: 0;">
                    Học Tập Tin Học
                </p>
            </div>
        </body>
    </html>
    """
    await EmailService._send(email, subject, html_body)
