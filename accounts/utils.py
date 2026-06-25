import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTP, User

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(user, otp_code):
    """Send OTP via email"""
    subject = 'Verify Your Email - LMS'
    message = f"""
    Hello {user.first_name or user.username},

    Thank you for registering with our Learning Management System.

    Your OTP verification code is: {otp_code}

    This code will expire in 10 minutes.

    If you didn't request this, please ignore this email.

    Best regards,
    LMS Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def create_and_send_otp(user):
    """Create OTP and send to user"""
    # Delete any existing unused OTPs
    OTP.objects.filter(user=user, is_used=False).delete()
    
    # Generate new OTP
    otp_code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    otp = OTP.objects.create(
        user=user,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    # Send email
    send_otp_email(user, otp_code)
    
    return otp

def verify_otp(user, otp_code):
    """Verify OTP for user"""
    try:
        otp = OTP.objects.get(user=user, otp_code=otp_code, is_used=False)
        if otp.is_valid():
            otp.is_used = True
            otp.save()
            
            # Activate user
            user.is_active = True
            user.is_email_verified = True
            user.save()
            
            return True, "Email verified successfully!"
        else:
            return False, "OTP has expired. Please request a new one."
    except OTP.DoesNotExist:
        return False, "Invalid OTP. Please try again."