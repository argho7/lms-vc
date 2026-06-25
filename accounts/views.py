from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse  # Add this import
from .forms import RegistrationForm, LoginForm, OTPVerificationForm, ResendOTPForm
from .models import User, OTP
from .utils import create_and_send_otp, verify_otp

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('assignments:dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verification
            user.save()
            
            # Send OTP
            create_and_send_otp(user)
            
            # Store user ID in session for verification
            request.session['pending_user_id'] = user.id
            
            messages.success(
                request,
                f'Registration successful! Please check your email ({user.email}) for OTP verification.'
            )
            # Use the namespace in redirect
            return redirect('accounts:verify_otp')  # Changed from 'verify_otp' to 'accounts:verify_otp'
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def verify_otp_view(request):
    """OTP verification view"""
    # Get pending user from session
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending registration found. Please register again.')
        return redirect('accounts:register')  # Changed from 'register' to 'accounts:register'
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please register again.')
        return redirect('accounts:register')  # Changed from 'register' to 'accounts:register'
    
    # Check if OTP expired
    try:
        latest_otp = OTP.objects.filter(user=user, is_used=False).latest('created_at')
        is_expired = not latest_otp.is_valid()
    except OTP.DoesNotExist:
        is_expired = True
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            success, message = verify_otp(user, otp_code)
            
            if success:
                # Log the user in
                login(request, user)
                # Clear session
                del request.session['pending_user_id']
                messages.success(request, 'Email verified successfully! Welcome to LMS.')
                return redirect('assignments:dashboard')  # Changed to assignments:dashboard
            else:
                messages.error(request, message)
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'email': user.email,
        'is_expired': is_expired
    })

def resend_otp(request):
    """Resend OTP view"""
    if request.method == 'POST':
        form = ResendOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=False)
                create_and_send_otp(user)
                
                # Store user ID in session
                request.session['pending_user_id'] = user.id
                
                messages.success(request, f'New OTP sent to {email}. Please check your email.')
                return redirect('accounts:verify_otp')  # Changed from 'verify_otp' to 'accounts:verify_otp'
            except User.DoesNotExist:
                messages.error(request, 'No pending registration found with this email.')
    else:
        form = ResendOTPForm()
    
    return render(request, 'accounts/resend_otp.html', {'form': form})

def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('assignments:dashboard')  # Changed to assignments:dashboard
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                        return redirect('assignments:dashboard')  # Changed to assignments:dashboard
                    else:
                        messages.error(request, 'Your account is not verified. Please check your email for OTP.')
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')  # Changed from 'login' to 'accounts:login'