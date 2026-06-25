from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_email_verified', 'is_active']
    list_filter = ['is_email_verified', 'is_active', 'is_student', 'is_teacher']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('phone', 'profile_picture', 'bio')}),
        ('Verification', {'fields': ('is_email_verified',)}),
        ('Role', {'fields': ('is_student', 'is_teacher')}),
    )

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used']