from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:course_id>/', views.checkout, name='checkout'),
    path('initiate/<int:course_id>/', views.initiate_payment, name='initiate_payment'),
    path('success/', views.payment_success, name='payment_success'),
    path('fail/', views.payment_fail, name='payment_fail'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('ipn/', views.payment_ipn, name='payment_ipn'),
]