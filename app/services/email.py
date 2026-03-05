"""SMTP 邮件发送服务（用于 Guestbook PIN 码验证）"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


def send_pin_email(to_email: str, nickname: str, pin: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【BBoyApp】你的留言验证码：{pin}"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    text = f"你好 {nickname}，\n\n你的验证码是：{pin}\n\n验证码 10 分钟内有效。"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#f97316">BBoyApp 留言验证码</h2>
      <p>你好 <strong>{nickname}</strong>，</p>
      <p>你的验证码是：</p>
      <div style="font-size:2rem;font-weight:bold;letter-spacing:.5rem;
                  background:#fff7ed;border:2px solid #f97316;border-radius:8px;
                  padding:16px 32px;display:inline-block">{pin}</div>
      <p style="color:#6b7280;font-size:.875rem">验证码 10 分钟内有效，请勿泄露给他人。</p>
    </div>
    """
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, to_email, msg.as_string())
