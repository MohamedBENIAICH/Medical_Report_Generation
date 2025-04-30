import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta

# Load environment variables with verbose logging
print("\n=== Loading environment variables ===")
env_loaded = load_dotenv()
print(f".env file loaded: {env_loaded}")

# Email configuration with fallback values
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET", "08910e79b19354e2c69c2076e7f4cc49d0454ed745d549400ec2c8432b099c74")

# Debug: Print all email configuration
print("\n=== Email Configuration ===")
print(f"SMTP_SERVER: {SMTP_SERVER}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SENDER_EMAIL: {SENDER_EMAIL}")
print(f"SENDER_PASSWORD: {'*' * len(SENDER_PASSWORD) if SENDER_PASSWORD else 'None'}")
print(f"JWT_SECRET: {'*' * len(JWT_SECRET) if JWT_SECRET else 'None'}")
print("==========================\n")

def send_verification_email(email, username):
    """Send email verification link to new user"""
    try:
        print(f"\n=== Attempting to send verification email to {email} ===")
        
        # Validate email configuration
        if not all([SENDER_EMAIL, SENDER_PASSWORD]):
            print("❌ ERROR: Missing email credentials!")
            print(f"- SENDER_EMAIL: {'Provided' if SENDER_EMAIL else 'Missing'}")
            print(f"- SENDER_PASSWORD: {'Provided' if SENDER_PASSWORD else 'Missing'}")
            return False

        # Create verification token
        token = jwt.encode(
            {
                'email': email,
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            JWT_SECRET,
            algorithm='HS256'
        )
        
        verification_link = f"http://localhost:8501/verify?token={token}"
        print(f"Generated verification link: {verification_link}")

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Verify your email address"
        
        body = f"""
        Hello {username},
        
        Thank you for registering with Medical Report Generator. 
        Please click the link below to verify your email address:
        
        {verification_link}
        
        This link will expire in 24 hours.
        
        Best regards,
        Medical Report Generator Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email with detailed error handling
        print("\n⏳ Attempting to send email...")
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                print("✅ Email sent successfully!")
                return True
        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP Authentication Failed - Check your email credentials")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False
    finally:
        print("=== Email sending process completed ===\n")

def send_password_reset_email(email):
    """Send password reset link to user"""
    try:
        print(f"\n=== Attempting to send password reset to {email} ===")
        
        if not all([SENDER_EMAIL, SENDER_PASSWORD]):
            print("❌ ERROR: Missing email credentials!")
            return False

        # Create reset token
        token = jwt.encode(
            {
                'email': email,
                'exp': datetime.utcnow() + timedelta(hours=1)
            },
            JWT_SECRET,
            algorithm='HS256'
        )
        
        reset_link = f"http://localhost:8501/reset-password?token={token}"
        print(f"Generated reset link: {reset_link}")

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Reset your password"
        
        body = f"""
        Hello,
        
        You have requested to reset your password. Please click the link below:
        
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Medical Report Generator Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print("\n⏳ Attempting to send email...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print("✅ Password reset email sent successfully!")
            return True
            
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Authentication Failed - Check your email credentials")
        return False
    except Exception as e:
        print(f"❌ Error sending password reset email: {str(e)}")
        return False
    finally:
        print("=== Password reset process completed ===\n")

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        print(f"✅ Token verified for {payload.get('email')}")
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return None
    except jwt.InvalidTokenError:
        print("❌ Invalid token")
        return None