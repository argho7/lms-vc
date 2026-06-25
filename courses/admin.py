from django.contrib import admin
from .models import Course, CourseModule, Lesson

# Register your models here.

admin.site.register(Course)
admin.site.register(CourseModule)
admin.site.register(Lesson)