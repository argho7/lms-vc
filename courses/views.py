from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Course, CourseModule, Lesson

def course_list(request):
    """Display all available courses"""
    # Get filter parameters
    category = request.GET.get('category')
    level = request.GET.get('level')
    search = request.GET.get('search')
    
    # Start with all courses
    courses = Course.objects.all().order_by('-created_at')
    
    # Apply filters
    if category:
        courses = courses.filter(category=category)
    if level:
        courses = courses.filter(level=level)
    if search:
        courses = courses.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Get categories and levels for filter dropdowns
    categories = Course.CATEGORY_CHOICES
    levels = Course._meta.get_field('level').choices
    
    context = {
        'courses': courses,
        'categories': categories,
        'levels': levels,
        'current_category': category,
        'current_level': level,
        'search_query': search,
    }
    
    return render(request, 'courses/course_list.html', context)

def course_detail(request, course_id):
    """Display course details with modules and lessons"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = course.is_enrolled(request.user)
    
    # Get modules and lessons
    modules = course.modules.all().prefetch_related('lessons')
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'modules': modules,
        'enrollment_count': course.enrollment_count(),
    }
    
    return render(request, 'courses/course_detail.html', context)

@login_required
def my_courses(request):
    """Display courses the user is enrolled in"""
    enrolled_courses = request.user.enrolled_courses.all()
    
    # Get progress for each course
    courses_with_progress = []
    for course in enrolled_courses:
        try:
            enrollment = course.enrollments.get(user=request.user)
            progress = enrollment.progress
        except:
            progress = 0
        courses_with_progress.append({
            'course': course,
            'progress': progress
        })
    
    context = {
        'courses': courses_with_progress,
    }
    
    return render(request, 'courses/my_courses.html', context)

@login_required
def enroll_free_course(request, course_id):
    """Enroll in a free course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if course.is_enrolled(request.user):
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('courses:course_detail', course_id=course.id)
    
    # Check if course is free
    if not course.is_free and course.price > 0:
        messages.error(request, 'This course requires payment. Please proceed to checkout.')
        return redirect('payments:checkout', course_id=course.id)
    
    # Enroll the user
    course.students.add(request.user)
    from payments.models import Enrollment
    Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'status': 'active'}
    )
    
    messages.success(request, f'Successfully enrolled in {course.title}!')
    return redirect('courses:course_detail', course_id=course.id)

@login_required
def course_progress(request, course_id):
    """Track and update course progress"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check enrollment
    if not course.is_enrolled(request.user):
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('courses:course_detail', course_id=course.id)
    
    try:
        from payments.models import Enrollment
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except:
        enrollment = None
    
    if request.method == 'POST':
        # Update progress (for example, when a lesson is completed)
        progress = request.POST.get('progress')
        if progress and enrollment:
            enrollment.progress = min(int(progress), 100)
            enrollment.save()
            messages.success(request, 'Progress updated!')
            return redirect('courses:course_detail', course_id=course.id)
    
    # Get all lessons count
    total_lessons = 0
    for module in course.modules.all():
        total_lessons += module.lessons.count()
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'total_lessons': total_lessons,
    }
    
    return render(request, 'courses/course_progress.html', context)