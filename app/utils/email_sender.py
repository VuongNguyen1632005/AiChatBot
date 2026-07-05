import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

async def send_otp_email(email: str, otp: str) -> None:
    """
    Gửi email chứa OTP cho người dùng qua SMTP sử dụng smtplib (non-blocking).
    """
    # Nếu không cấu hình SMTP trong file .env, ta sẽ giả lập (mock) ghi vào console để hỗ trợ dev
    if not all([settings.MAIL_SERVER, settings.MAIL_USERNAME, settings.MAIL_PASSWORD]):
        print(f"\n==========================================")
        print(f"📧 [EMAIL MOCK] Gửi OTP '{otp}' đến {email}")
        print(f"==========================================\n")
        return

    def _send():
        msg = MIMEMultipart()
        msg["From"] = settings.MAIL_FROM or settings.MAIL_USERNAME
        msg["To"] = email
        msg["Subject"] = "Mã OTP đặt lại mật khẩu"
        
        body = f"""Chào bạn,

Mã OTP để đặt lại mật khẩu của bạn là: {otp}

Mã này có hiệu lực trong vòng 5 phút (300 giây). Vui lòng không chia sẻ mã này với bất kỳ ai.

Trân trọng,
Đội ngũ phát triển.
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # Tạo kết nối SMTP
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        try:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(msg["From"], email, msg.as_string())
        finally:
            server.quit()

    # Thực thi đồng bộ _send trong một worker thread để không block event loop của FastAPI
    await asyncio.to_thread(_send)
