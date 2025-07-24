import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_host = settings.EMAIL_HOST
        self.smtp_port = settings.EMAIL_PORT
        self.smtp_username = settings.EMAIL_USERNAME
        self.smtp_password = settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_FROM
        
        # Check if email is configured
        self.is_configured = all([
            self.smtp_host,
            self.smtp_username,
            self.smtp_password
        ])
        
        if not self.is_configured:
            logger.warning("Email service not configured. OTP emails will not be sent.")
    
    def send_otp_email(self, to_email: str, otp: str) -> bool:
        """Send OTP via email."""
        if not self.is_configured:
            # Log OTP for development (remove in production)
            logger.info(f"OTP for {to_email}: {otp}")
            return True  # Return True for development
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Your Coinfrs Login Code'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Email body
            text_content = f"""
Your Coinfrs login code is: {otp}

This code will expire in 5 minutes.

If you didn't request this code, please ignore this email.
"""
            
            html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
      <h2 style="color: #333;">Your Coinfrs Login Code</h2>
      <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <p style="font-size: 32px; font-weight: bold; text-align: center; letter-spacing: 5px; margin: 0;">
          {otp}
        </p>
      </div>
      <p style="color: #666;">This code will expire in 5 minutes.</p>
      <p style="color: #666; font-size: 14px;">
        If you didn't request this code, please ignore this email.
      </p>
    </div>
  </body>
</html>
"""
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"OTP email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str) -> bool:
        """Send welcome email to new users."""
        if not self.is_configured:
            return True  # Skip in development
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Welcome to Coinfrs'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            text_content = """
Welcome to Coinfrs!

Thank you for joining us. You can now start managing your digital asset portfolios.

Best regards,
The Coinfrs Team
"""
            
            html_content = """
<html>
  <body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto;">
      <h1 style="color: #333;">Welcome to Coinfrs!</h1>
      <p>Thank you for joining us. You can now start managing your digital asset portfolios.</p>
      <p>Best regards,<br>The Coinfrs Team</p>
    </div>
  </body>
</html>
"""
            
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False


# Singleton instance
email_service = None

def get_email_service() -> EmailService:
    """Get or create the email service instance."""
    global email_service
    if email_service is None:
        email_service = EmailService()
    return email_service