from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('enroll/<int:course_id>/', views.enroll_free_course, name='enroll_free'),
    path('progress/<int:course_id>/', views.course_progress, name='course_progress'),
]