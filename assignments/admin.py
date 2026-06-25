from django.contrib import admin
from .models import Course, Assignment, Submission

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'created_at']
    filter_horizontal = ['students']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'due_date', 'status', 'max_score']
    list_filter = ['status', 'course', 'due_date']
    search_fields = ['title']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'submitted_at', 'score']
    list_filter = ['assignment', 'submitted_at']
    search_fields = ['student__username', 'assignment__title']