from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, F

class Mentor(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    EXPERTISE_CHOICES = [
        ('SPIRITUAL', 'Spiritual Growth & Ministry'),
        ('CAREER', 'Career & Professional Development'),
        ('LEADERSHIP', 'Leadership & Governance'),
        ('RELATIONSHIP', 'Family & Relationship'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    expertise = models.CharField(max_length=20, choices=EXPERTISE_CHOICES)
    max_mentees = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"{self.name} ({self.get_expertise_display()})"

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    banner = models.ImageField(upload_to='course_banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    youtube_link = models.URLField(help_text="YouTube URL, e.g., https://www.youtube.com/watch?v=...")
    content = models.TextField(help_text="WYSIWYG/HTML content for the module")

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"

class Assessment(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='assessment')
    title = models.CharField(max_length=200)
    passing_score = models.PositiveIntegerField(default=70, help_text="Percentage score required to pass (0-100)")

    def __str__(self):
        return f"Assessment: {self.title} ({self.module.title})"

class AssessmentQuestion(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice'),
        ('TEXT', 'Short/Long Answer'),
    ]
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='MCQ')

    def __str__(self):
        return f"{self.assessment.title} - {self.question_text[:50]}"

class AssessmentChoice(models.Model):
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentees')

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.email or self.user.username} enrolled in {self.course.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.mentor:
            self.mentor = self.assign_mentor()
            if self.mentor:
                # save update fields to avoid infinite loops
                super().save(update_fields=['mentor'])

    def assign_mentor(self):
        from user_authentication.models import UserProfile
        try:
            profile = self.user.profile
            user_gender = profile.gender
            user_interests = profile.interests
        except UserProfile.DoesNotExist:
            return None

        # 1. Match both gender and expertise, annotated with active mentees count
        matching_mentors = Mentor.objects.filter(
            expertise=user_interests,
            gender=user_gender
        ).annotate(
            num_mentees=Count('mentees')
        ).filter(
            num_mentees__lt=F('max_mentees')
        ).order_by('num_mentees')

        if matching_mentors.exists():
            return matching_mentors.first()

        # 2. Fallback: match expertise only
        fallback_mentors = Mentor.objects.filter(
            expertise=user_interests
        ).annotate(
            num_mentees=Count('mentees')
        ).filter(
            num_mentees__lt=F('max_mentees')
        ).order_by('num_mentees')

        if fallback_mentors.exists():
            return fallback_mentors.first()

        return None

class ModuleProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='progress_records')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user.username} - {self.module.title} - {'Completed' if self.completed else 'In Progress'}"

class AssessmentSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_submissions')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(help_text="Percentage score achieved (0-100)")
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.assessment.module.title} - Score: {self.score}%"
