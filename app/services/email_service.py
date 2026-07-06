import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class EmailService:
    """
    Dịch vụ gửi email của hệ thống.
    """
    @staticmethod
    async def send_verify_email(email: str, token: str) -> None:
        """
        Gửi email chứa liên kết xác thực tài khoản (non-blocking).
        """
        # Nếu không cấu hình SMTP trong file .env, ta sẽ giả lập (mock) ghi vào console để hỗ trợ dev
        if not all([settings.MAIL_SERVER, settings.MAIL_USERNAME, settings.MAIL_PASSWORD]):
            print(f"\n==========================================")
            print(f"📧 [EMAIL MOCK] Gửi liên kết xác thực email đến {email}")
            print(f"🔗 Link: http://127.0.0.1:8000/api/v1/auth/verify-email?token={token}")
            print(f"==========================================\n")
            return

        def _send():
            msg = MIMEMultipart()
            msg["From"] = settings.MAIL_FROM or settings.MAIL_USERNAME
            msg["To"] = email
            msg["Subject"] = "Xác thực tài khoản của bạn"
            
            body = f"""Chào bạn,

Vui lòng nhấp vào liên kết dưới đây để xác thực tài khoản của bạn:
http://127.0.0.1:8000/api/v1/auth/verify-email?token={token}

Liên kết này có hiệu lực trong vòng 24 giờ.

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
