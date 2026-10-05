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
    is_paid = models.BooleanField(default=False)
    price = models.PositiveIntegerField(default=0, blank=True, help_text="Price in Naira (e.g., 5000)")
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

class CoursePayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField(default=0)
    payment_date = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} paid {self.amount} for {self.course.title} - Approved: {self.approved}"

class Certificate(models.Model):
    certificate_code = models.CharField(max_length=64, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-issued_at']

    def __str__(self):
        return f"Certificate for {self.user.get_full_name() or self.user.username} - {self.course.title} ({self.certificate_code})"

    def save(self, *args, **kwargs):
        if not self.certificate_code:
            import uuid
            self.certificate_code = f"CAN-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def generate_pdf(self, save=True):
        import re
        from .certificate_generator import generate_leadership_certificate_pdf
        from django.core.files.base import ContentFile
        pdf_bytes = generate_leadership_certificate_pdf(self)
        if save:
            clean_username = re.sub(r'[^a-zA-Z0-9_-]', '_', self.user.username)
            filename = f"Certificate_{self.certificate_code}_{clean_username}.pdf"
            self.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        return pdf_bytes

    def get_or_create_pdf(self):
        if self.pdf_file and self.pdf_file.name:
            try:
                self.pdf_file.open('rb')
                content = self.pdf_file.read()
                self.pdf_file.close()
                if content and content.startswith(b'%PDF'):
                    return content
            except Exception:
                pass
            # If reading from remote storage failed, generate in-memory cleanly
            return self.generate_pdf(save=False)
        return self.generate_pdf(save=True)

    @classmethod
    def check_and_unlock(cls, user, course):
        """
        Unlocks and returns (certificate, newly_created) if the user has completed all modules in the course.
        Returns (None, False) if the course has no modules or not all modules are completed.
        """
        if not user or not user.is_authenticated:
            return None, False

        total_modules = course.modules.count()
        if total_modules == 0:
            return None, False

        completed_count = ModuleProgress.objects.filter(
            user=user,
            module__course=course,
            completed=True
        ).count()

        if completed_count >= total_modules:
            cert, created = cls.objects.get_or_create(user=user, course=course)
            if created or not cert.pdf_file:
                try:
                    cert.generate_pdf(save=True)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error auto-generating certificate PDF for {cert}: {e}")
            return cert, created

        return None, False

