from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views  # Add this

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('assignments.urls')),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('payment/', include('payments.urls')),
    
    # Add these for login/logout as fallback
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # path('accounts/', include('django.contrib.auth.urls')),