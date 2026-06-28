import re
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from main.Paystack import PayStack
from .models import (
    Course, Module, Mentor, CourseEnrollment,
    ModuleProgress, Assessment, AssessmentQuestion,
    AssessmentChoice, AssessmentSubmission, CoursePayment
)

def get_youtube_id(url):
    if not url:
        return None
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def course_list_view(request):
    courses = Course.objects.all()
    enrolled_course_ids = []
    if request.user.is_authenticated:
        enrolled_course_ids = list(
            CourseEnrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        )
    
    # Annotate courses with enrollment status
    for course in courses:
        course.is_enrolled = course.id in enrolled_course_ids

    return render(request, 'course/course_list.html', {
        'courses': courses,
    })

def course_detail_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    modules = course.modules.order_by('order')
    
    is_enrolled = False
    has_paid = False
    if request.user.is_authenticated:
        is_enrolled = CourseEnrollment.objects.filter(user=request.user, course=course).exists()
        if course.is_paid:
            has_paid = CoursePayment.objects.filter(user=request.user, course=course, approved=True).exists()

    return render(request, 'course/course_detail.html', {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
        'has_paid': has_paid,
    })

@login_required
def enroll_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    
    if course.is_paid:
        has_paid = CoursePayment.objects.filter(user=request.user, course=course, approved=True).exists()
        if not has_paid:
            return redirect('course:initiate_payment', course_id=course.id)

    enrollment, created = CourseEnrollment.objects.get_or_create(user=request.user, course=course)
    
    if created:
        if enrollment.mentor:
            messages.success(
                request,
                f"Successfully enrolled in {course.title}! You have been matched with Mentor: {enrollment.mentor.name} ({enrollment.mentor.email})."
            )
        else:
            messages.success(
                request,
                f"Successfully enrolled in {course.title}! Our team will match you with a mentor shortly."
            )
    else:
        messages.info(request, f"You are already enrolled in {course.title}.")

    return redirect('course:dashboard')

@login_required
def dashboard_view(request):
    enrollments = CourseEnrollment.objects.filter(user=request.user).select_related('course', 'mentor')
    
    # Calculate progress for each enrollment
    for enrollment in enrollments:
        total_modules = enrollment.course.modules.count()
        completed_modules = ModuleProgress.objects.filter(
            user=request.user,
            module__course=enrollment.course,
            completed=True
        ).count()
        
        enrollment.progress_percent = int((completed_modules / total_modules) * 100) if total_modules > 0 else 0
        enrollment.completed_modules = completed_modules
        enrollment.total_modules = total_modules

    # Recommended courses (not enrolled in)
    enrolled_ids = [e.course_id for e in enrollments]
    recommended_courses = Course.objects.exclude(id__in=enrolled_ids)[:3]

    return render(request, 'course/dashboard.html', {
        'enrollments': enrollments,
        'recommended_courses': recommended_courses,
    })

@login_required
def module_view(request, course_id, module_id):
    enrollment = get_object_or_404(CourseEnrollment, user=request.user, course_id=course_id)
    module = get_object_or_404(Module, pk=module_id, course_id=course_id)
    
    # Syllabus side panel list
    modules = list(enrollment.course.modules.order_by('order'))
    completed_module_ids = set(
        ModuleProgress.objects.filter(
            user=request.user,
            module__course_id=course_id,
            completed=True
        ).values_list('module_id', flat=True)
    )
    
    for m in modules:
        m.completed = m.id in completed_module_ids

    # Video details
    youtube_id = get_youtube_id(module.youtube_link)

    # Assessment details
    assessment = getattr(module, 'assessment', None)
    assessment_passed = False
    last_submission = None
    
    if assessment:
        last_submission = AssessmentSubmission.objects.filter(
            user=request.user,
            assessment=assessment
        ).order_by('-submitted_at').first()
        assessment_passed = last_submission.passed if last_submission else False

    # Find next module (for navigation link)
    next_module = enrollment.course.modules.filter(order__gt=module.order).order_by('order').first()

    return render(request, 'course/module_detail.html', {
        'course': enrollment.course,
        'module': module,
        'modules': modules,
        'youtube_id': youtube_id,
        'assessment': assessment,
        'assessment_passed': assessment_passed,
        'last_submission': last_submission,
        'next_module': next_module,
    })

@login_required
def submit_assessment_view(request, course_id, module_id):
    if request.method != 'POST':
        return redirect('course:module_detail', course_id=course_id, module_id=module_id)
        
    enrollment = get_object_or_404(CourseEnrollment, user=request.user, course_id=course_id)
    module = get_object_or_404(Module, pk=module_id, course_id=course_id)
    assessment = get_object_or_404(Assessment, module=module)
    
    questions = assessment.questions.all()
    if not questions.exists():
        # Empty assessment is automatically marked as passed
        AssessmentSubmission.objects.create(user=request.user, assessment=assessment, score=100.0, passed=True)
        ModuleProgress.objects.update_or_create(
            user=request.user,
            module=module,
            defaults={'completed': True, 'completed_at': timezone.now()}
        )
        messages.success(request, "Assessment submitted successfully!")
        return redirect('course:module_detail', course_id=course_id, module_id=module_id)

    total_graded_questions = 0
    correct_graded_questions = 0

    for q in questions:
        if q.question_type == 'MCQ':
            total_graded_questions += 1
            selected_choice_id = request.POST.get(f'question_{q.id}')
            if selected_choice_id:
                try:
                    choice = AssessmentChoice.objects.get(pk=selected_choice_id, question=q)
                    if choice.is_correct:
                        correct_graded_questions += 1
                except AssessmentChoice.DoesNotExist:
                    pass
        else:
            # TEXT questions are self-reflection and automatically awarded full points for submitting
            # (or admin can grade them manually later).
            total_graded_questions += 1
            user_text_response = request.POST.get(f'question_{q.id}')
            if user_text_response and user_text_response.strip():
                correct_graded_questions += 1

    score = 100.0
    if total_graded_questions > 0:
        score = (correct_graded_questions / total_graded_questions) * 100.0

    passed = score >= assessment.passing_score
    
    AssessmentSubmission.objects.create(
        user=request.user,
        assessment=assessment,
        score=score,
        passed=passed
    )

    if passed:
        ModuleProgress.objects.update_or_create(
            user=request.user,
            module=module,
            defaults={'completed': True, 'completed_at': timezone.now()}
        )
        messages.success(request, f"Congratulations! You passed the assessment with a score of {score:.1f}%!")
    else:
        messages.error(
            request,
            f"You scored {score:.1f}%, which is below the passing score of {assessment.passing_score}%. Please try again."
        )

    return redirect('course:module_detail', course_id=course_id, module_id=module_id)

@login_required
def complete_module_view(request, course_id, module_id):
    if request.method == 'POST':
        enrollment = get_object_or_404(CourseEnrollment, user=request.user, course_id=course_id)
        module = get_object_or_404(Module, pk=module_id, course_id=course_id)
        ModuleProgress.objects.update_or_create(
            user=request.user,
            module=module,
            defaults={'completed': True, 'completed_at': timezone.now()}
        )
        messages.success(request, f"Module '{module.title}' marked as completed!")
        
        # Redirect to next module if available
        next_module = enrollment.course.modules.filter(order__gt=module.order).order_by('order').first()
        if next_module:
            return redirect('course:module_detail', course_id=course_id, module_id=next_module.id)
        else:
            return redirect('course:dashboard')
    return redirect('course:module_detail', course_id=course_id, module_id=module_id)

@login_required
def initiate_course_payment_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_paid:
        messages.info(request, "This course is free. You can enroll directly.")
        return redirect('course:enroll', course_id=course.id)

    # Check if they already have an approved payment
    has_paid = CoursePayment.objects.filter(user=request.user, course=course, approved=True).exists()
    if has_paid:
        messages.info(request, "You have already paid for this course.")
        return redirect('course:enroll', course_id=course.id)

    # Create a CoursePayment entry
    course_payment = CoursePayment.objects.create(
        user=request.user,
        course=course,
        amount=course.price
    )

    # Determine callback URL dynamically
    callback_url = request.build_absolute_uri(reverse('course:verify_payment'))

    # Metadata for Paystack webhook/callback
    metadata = {
        'transaction_type': 'course_payment',
        'course_payment_id': course_payment.id
    }

    # Paystack amount is in kobo (multiply by 100)
    redirect_url = PayStack.generate_checkout_url(
        email=request.user.email,
        amount=course.price * 100,
        ref=course_payment.id,
        metadata=metadata,
        callback_url=callback_url
    )

    if redirect_url:
        return redirect(redirect_url)
    else:
        messages.error(request, "Could not initialize payment gateway. Please try again later.")
        return redirect('course:course_detail', course_id=course.id)

def verify_course_payment_view(request):
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, "No reference found for transaction.")
        return redirect('course:course_list')

    payment_info = PayStack.verify_payment(reference)
    if payment_info and payment_info.get('status') == 'success':
        metadata = payment_info.get('metadata', {})
        if metadata.get('transaction_type') == 'course_payment':
            payment_id = metadata.get('course_payment_id')
            try:
                course_payment = CoursePayment.objects.get(id=payment_id)
                if not course_payment.approved:
                    course_payment.approved = True
                    course_payment.save()
                    
                    # Create enrollment since they have successfully paid!
                    enrollment, created = CourseEnrollment.objects.get_or_create(
                        user=course_payment.user,
                        course=course_payment.course
                    )
                    
                    # Add enrollment success message matching enroll_view details
                    if created:
                        if enrollment.mentor:
                            messages.success(
                                request,
                                f"Payment successful! You have enrolled in {course_payment.course.title} and matched with Mentor: {enrollment.mentor.name} ({enrollment.mentor.email})."
                            )
                        else:
                            messages.success(
                                request,
                                f"Payment successful! You have enrolled in {course_payment.course.title}. Our team will match you with a mentor shortly."
                            )
                    else:
                        messages.success(request, f"Payment successful! You are enrolled in {course_payment.course.title}.")
                
                return redirect('course:dashboard')
            except CoursePayment.DoesNotExist:
                messages.error(request, "Associated course payment record not found.")
                return redirect('course:course_list')
        else:
            messages.error(request, "Invalid transaction verification.")
            return redirect('course:course_list')
    else:
        messages.error(request, "Payment verification failed or was cancelled.")
        return redirect('course:course_list')
