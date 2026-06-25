from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from courses.models import Course
from .models import Payment, Enrollment
from django.conf import settings

@login_required
def checkout(request, course_id):
    """Checkout page"""
    course = get_object_or_404(Course, id=course_id)
    
    if course.is_enrolled(request.user):
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('courses:course_detail', course_id=course.id)
    
    if course.is_free or course.price == 0:
        course.students.add(request.user)
        Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'status': 'active'}
        )
        messages.success(request, f'Successfully enrolled in {course.title}!')
        return redirect('courses:course_detail', course_id=course.id)
    
    return render(request, 'payments/checkout.html', {
        'course': course,
        'amount': course.price
    })

@login_required
def initiate_payment(request, course_id):
    """Redirect to SSLCommerz payment page"""
    course = get_object_or_404(Course, id=course_id)
    
    if course.is_enrolled(request.user):
        messages.warning(request, 'You are already enrolled in this course.')
        return redirect('courses:course_detail', course_id=course.id)
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        course=course,
        amount=course.price,
        status='pending'
    )
    
    # SSLCommerz sandbox credentials
    store_id = settings.SSLCOMMERZ_STORE_ID
    store_pass = settings.SSLCOMMERZ_STORE_PASSWORD
    url = 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php'
    
    # Generate transaction ID
    tran_id = f"LMS_{request.user.id}_{course.id}_{int(timezone.now().timestamp())}"
    
    # Get user name
    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not full_name:
        full_name = request.user.username
    
    # Prepare data for SSLCommerz
    post_data = {
        'store_id': store_id,
        'store_passwd': store_pass,
        'total_amount': str(float(course.price)),
        'currency': 'BDT',
        'tran_id': tran_id,
        'success_url': request.build_absolute_uri('/payment/success/'),
        'fail_url': request.build_absolute_uri('/payment/fail/'),
        'cancel_url': request.build_absolute_uri('/payment/cancel/'),
        'ipn_url': request.build_absolute_uri('/payment/ipn/'),
        'cus_name': full_name[:50],
        'cus_email': request.user.email[:50],
        'cus_phone': request.user.phone or '01700000000',
        'cus_add1': 'N/A',
        'cus_city': 'Dhaka',
        'cus_country': 'Bangladesh',
        'shipping_method': 'NO',
        'product_name': course.title[:100],
        'product_category': course.category or 'general',
        'product_profile': 'general',
    }
    
    payment.transaction_id = tran_id
    payment.save()
    
    try:
        response = requests.post(url, data=post_data, timeout=30)
        response_data = response.json()
        
        if response_data.get('status') == 'SUCCESS':
            # Redirect to SSLCommerz payment page with all options
            gateway_url = response_data.get('redirectGatewayURL')
            if gateway_url:
                return redirect(gateway_url)
            else:
                payment.status = 'failed'
                payment.save()
                messages.error(request, 'Payment initiation failed.')
                return redirect('payments:checkout', course_id=course.id)
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment initiation failed: {response_data.get("failedreason", "Unknown error")}')
            return redirect('payments:checkout', course_id=course.id)
            
    except Exception as e:
        payment.status = 'failed'
        payment.save()
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('payments:checkout', course_id=course.id)

@csrf_exempt
def payment_ipn(request):
    """SSLCommerz IPN handler"""
    if request.method == 'POST':
        post_data = request.POST.dict()
        tran_id = post_data.get('tran_id')
        
        if not tran_id:
            return HttpResponse('Transaction ID not found', status=400)
        
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
        except Payment.DoesNotExist:
            return HttpResponse('Payment not found', status=404)
        
        # Verify with SSLCommerz
        verify_url = 'https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php'
        validation_data = {
            'val_id': post_data.get('val_id'),
            'store_id': settings.SSLCOMMERZ_STORE_ID , 
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
            'format': 'json'
        }
        
        try:
            response = requests.get(verify_url, params=validation_data, timeout=30)
            verify_data = response.json()
            
            if verify_data.get('status') == 'VALID':
                payment.status = 'success'
                payment.paid_at = timezone.now()
                payment.save()
                
                # Enroll user
                payment.course.students.add(payment.user)
                Enrollment.objects.get_or_create(
                    user=payment.user,
                    course=payment.course,
                    defaults={'status': 'active'}
                )
                return HttpResponse('Verified', status=200)
            else:
                payment.status = 'failed'
                payment.save()
                return HttpResponse('Invalid', status=400)
                
        except Exception:
            payment.status = 'failed'
            payment.save()
            return HttpResponse('Error', status=500)
    
    return HttpResponse('Invalid request', status=400)

@login_required
def payment_success(request):
    """Payment success page"""
    tran_id = request.GET.get('tran_id')
    
    if tran_id:
        try:
            payment = Payment.objects.get(transaction_id=tran_id, user=request.user)
            if payment.status == 'pending':
                # Check with SSLCommerz if IPN didn't process
                payment.status = 'success'
                payment.paid_at = timezone.now()
                payment.save()
                payment.course.students.add(request.user)
                Enrollment.objects.get_or_create(
                    user=request.user,
                    course=payment.course,
                    defaults={'status': 'active'}
                )
            
            messages.success(request, f'Payment successful! You are now enrolled in {payment.course.title}.')
            return redirect('courses:course_detail', course_id=payment.course.id)
            
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found.')
            return redirect('dashboard')
    
    messages.success(request, 'Payment successful!')
    return redirect('dashboard')

@login_required
def payment_fail(request):
    """Payment failure page"""
    messages.error(request, 'Payment failed. Please try again.')
    return render(request, 'payments/payment_fail.html')

@login_required
def payment_cancel(request):
    """Payment cancellation page"""
    messages.warning(request, 'Payment was canceled.')
    return render(request, 'payments/payment_cancel.html')