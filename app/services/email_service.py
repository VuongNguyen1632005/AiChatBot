import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Dịch vụ gửi email của hệ thống.
    """
    @staticmethod
    async def send_verify_email(email: str, token: str) -> None:
        """
        Gửi email chứa liên kết xác thực tài khoản (non-blocking).
        Mã lỗi sẽ được bắt và ghi log để không làm gián đoạn luồng đăng ký.
        """
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        # Nếu không cấu hình SMTP trong file .env, ta sẽ giả lập (mock) ghi vào console để hỗ trợ dev
        if not all([settings.MAIL_SERVER, settings.MAIL_USERNAME, settings.MAIL_PASSWORD]):
            print(f"\n==========================================")
            print(f"📧 [EMAIL MOCK] Gửi liên kết xác thực email đến {email}")
            print(f"🔗 Link: {link}")
            print(f"==========================================\n")
            return

        def _send():
            msg = MIMEMultipart()
            msg["From"] = settings.MAIL_FROM or settings.MAIL_USERNAME
            msg["To"] = email
            msg["Subject"] = "Xác thực tài khoản của bạn"
            
            html_content = f"""
            <html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                        <h2 style="color: #333333; text-align: center;">Xác thực tài khoản của bạn</h2>
                        <p>Chào bạn,</p>
                        <p>Cảm ơn bạn đã đăng ký tài khoản trên hệ thống. Vui lòng nhấn vào nút bên dưới để hoàn tất việc xác thực tài khoản của bạn:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{link}" style="background-color: #4CAF50; color: white; padding: 12px 25px; text-decoration: none; font-size: 16px; border-radius: 5px; display: inline-block; font-weight: bold;">Xác thực tài khoản</a>
                        </div>
                        <p style="color: #666666; font-size: 14px; text-align: center;">Liên kết này có hiệu lực trong vòng <strong>24 giờ</strong>.</p>
                        <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 20px 0;">
                        <p style="color: #999999; font-size: 12px;">Nếu nút bấm trên không hoạt động, bạn có thể copy và dán liên kết dưới đây vào trình duyệt:<br><a href="{link}" style="color: #4CAF50;">{link}</a></p>
                    </div>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # Tạo kết nối SMTP
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
            try:
                server.starttls()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(msg["From"], email, msg.as_string())
            finally:
                server.quit()

        try:
            # Thực thi đồng bộ _send trong một worker thread để không block event loop của FastAPI
            await asyncio.to_thread(_send)
        except Exception as e:
            logger.warning(f"⚠️ Lỗi gửi email xác thực đến {email}: {e}")
