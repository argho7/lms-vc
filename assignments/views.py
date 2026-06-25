from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.utils import timezone  # <-- IMPORTANT
from .models import Course, Assignment, Submission
from .forms import SubmissionForm


@login_required
def dashboard(request):
    # Get courses from the courses app
    enrolled_courses = request.user.enrolled_courses.all()
    teaching_courses = request.user.courses_taught.all()
    
    # Get assignments - for now, let's just get assignments for the courses
    # the user is enrolled in (you'll need to link assignments to courses)
    # For now, we'll keep it simple
    upcoming_assignments = []
    
    # Try to get assignments if they exist
    try:
        upcoming_assignments = Assignment.objects.filter(
            course__students=request.user,  # This uses assignments.Course
            status='published',
            due_date__gte=timezone.now()
        ).order_by('due_date')[:5]
    except:
        # If there's an error, just use an empty list
        upcoming_assignments = []
    
    context = {
        'enrolled_courses': enrolled_courses,
        'teaching_courses': teaching_courses,
        'upcoming_assignments': upcoming_assignments,
    }
    return render(request, 'assignments/dashboard.html', context)


# List all assignments for a course
class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return Assignment.objects.filter(course_id=course_id, status='published')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return context


# Detail view for a specific assignment
class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if the current user has already submitted
        try:
            submission = Submission.objects.get(
                assignment=self.object,
                student=self.request.user
            )
            context['submission'] = submission
            context['has_submitted'] = True
        except Submission.DoesNotExist:
            context['has_submitted'] = False
        return context


# Submit an assignment
@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if already submitted
    existing = Submission.objects.filter(assignment=assignment, student=request.user).first()
    if existing:
        messages.warning(request, 'You have already submitted this assignment.')
        return redirect('assignment_detail', pk=assignment_id)
    
    # Check if assignment is overdue
    if assignment.is_overdue():
        messages.error(request, 'This assignment is overdue. You cannot submit.')
        return redirect('assignment_detail', pk=assignment_id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('assignment_detail', pk=assignment_id)
    else:
        form = SubmissionForm()
    
    return render(request, 'assignments/submit_form.html', {
        'form': form,
        'assignment': assignment
    })