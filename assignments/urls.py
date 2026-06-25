from django.urls import path
from . import views

app_name = 'assignments'  # Make sure this exists

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # This defines the dashboard URL
    path('course/<int:course_id>/assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignment/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
]