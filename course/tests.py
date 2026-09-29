from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from user_authentication.models import UserProfile
from user_authentication.forms import RegisterForm
from course.models import (
    Mentor, Course, Module, Assessment,
    AssessmentQuestion, AssessmentChoice,
    CourseEnrollment, ModuleProgress, AssessmentSubmission,
    CoursePayment, Certificate
)

class CoursePlatformTestCase(TestCase):
    def setUp(self):
        # Create some Mentors
        self.mentor_male_spiritual = Mentor.objects.create(
            name="Brother John",
            email="john@example.com",
            gender="M",
            expertise="SPIRITUAL",
            max_mentees=2
        )
        self.mentor_female_spiritual = Mentor.objects.create(
            name="Sister Sarah",
            email="sarah@example.com",
            gender="F",
            expertise="SPIRITUAL",
            max_mentees=2
        )
        self.mentor_male_career = Mentor.objects.create(
            name="Mr. David",
            email="david@example.com",
            gender="M",
            expertise="CAREER",
            max_mentees=2
        )
        
        # Create a Course and a Module
        self.course = Course.objects.create(
            title="Spiritual Leadership",
            description="Deep dive into spiritual leadership."
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Module 1: The Call",
            order=1,
            youtube_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            content="<p>Introduction to the call of leadership.</p>"
        )

        # Create an Assessment with questions
        self.assessment = Assessment.objects.create(
            module=self.module,
            title="Syllabus 1 Quiz",
            passing_score=75
        )
        self.q1 = AssessmentQuestion.objects.create(
            assessment=self.assessment,
            question_text="Is leadership a call?",
            question_type="MCQ"
        )
        self.choice_yes = AssessmentChoice.objects.create(
            question=self.q1,
            choice_text="Yes",
            is_correct=True
        )
        self.choice_no = AssessmentChoice.objects.create(
            question=self.q1,
            choice_text="No",
            is_correct=False
        )

    def test_user_profile_creation_on_signup(self):
        # Test custom RegisterForm saves UserProfile
        form_data = {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'gender': 'F',
            'interests': 'SPIRITUAL',
            'occupation': 'Student',
            'location': 'Lagos, Nigeria'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        
        user = form.save()
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.gender, 'F')
        self.assertEqual(user.profile.interests, 'SPIRITUAL')
        self.assertEqual(user.profile.occupation, 'Student')
        self.assertEqual(user.profile.location, 'Lagos, Nigeria')

    def test_mentorship_matching_logic(self):
        # Register a female user with spiritual interest
        user_female = User.objects.create_user(
            username="female_user@example.com",
            email="female_user@example.com",
            password="testpassword"
        )
        UserProfile.objects.create(
            user=user_female,
            gender="F",
            interests="SPIRITUAL",
            occupation="Student",
            location="Abuja"
        )

        # Enroll in Course
        enrollment = CourseEnrollment.objects.create(user=user_female, course=self.course)
        
        # Verify she is matched with the Female Spiritual Mentor (Sister Sarah)
        self.assertEqual(enrollment.mentor, self.mentor_female_spiritual)

        # Register a male user with spiritual interest
        user_male = User.objects.create_user(
            username="male_user@example.com",
            email="male_user@example.com",
            password="testpassword"
        )
        UserProfile.objects.create(
            user=user_male,
            gender="M",
            interests="SPIRITUAL",
            occupation="Professional",
            location="Ibadan"
        )
        
        enrollment_male = CourseEnrollment.objects.create(user=user_male, course=self.course)
        
        # Verify he is matched with the Male Spiritual Mentor (Brother John)
        self.assertEqual(enrollment_male.mentor, self.mentor_male_spiritual)

    def test_mentorship_matching_fallback(self):
        # Test fallback when gender matching is full/not available
        # Fill capacity for Sister Sarah
        user1 = User.objects.create_user(username="u1@example.com", email="u1@example.com")
        UserProfile.objects.create(user=user1, gender="F", interests="SPIRITUAL")
        CourseEnrollment.objects.create(user=user1, course=self.course, mentor=self.mentor_female_spiritual)
        
        user2 = User.objects.create_user(username="u2@example.com", email="u2@example.com")
        UserProfile.objects.create(user=user2, gender="F", interests="SPIRITUAL")
        CourseEnrollment.objects.create(user=user2, course=self.course, mentor=self.mentor_female_spiritual)
        
        # Sister Sarah (F, SPIRITUAL) now has 2 mentees (max_mentees=2).
        # When a new female user registers with SPIRITUAL interest, she should fall back to Brother John (M, SPIRITUAL)
        user_new_female = User.objects.create_user(username="new_f@example.com", email="new_f@example.com")
        UserProfile.objects.create(user=user_new_female, gender="F", interests="SPIRITUAL")
        
        enrollment = CourseEnrollment.objects.create(user=user_new_female, course=self.course)
        
        # Should fall back to Brother John
        self.assertEqual(enrollment.mentor, self.mentor_male_spiritual)

    def test_grading_logic(self):
        user = User.objects.create_user(username="student@example.com", email="student@example.com")
        UserProfile.objects.create(user=user, gender="M", interests="CAREER")
        CourseEnrollment.objects.create(user=user, course=self.course)
        
        # Try submitting incorrect answer
        # Create submission simulation
        self.client.force_login(user)
        response = self.client.post(
            f'/courses/{self.course.id}/modules/{self.module.id}/submit_assessment/',
            {f'question_{self.q1.id}': self.choice_no.id}
        )
        
        # Verify submission exists and is failed
        sub = AssessmentSubmission.objects.filter(user=user, assessment=self.assessment).latest('submitted_at')
        self.assertEqual(sub.score, 0.0)
        self.assertFalse(sub.passed)
        # Check module progress is not marked completed
        progress_exists = ModuleProgress.objects.filter(user=user, module=self.module, completed=True).exists()
        self.assertFalse(progress_exists)

        # Try submitting correct answer
        response = self.client.post(
            f'/courses/{self.course.id}/modules/{self.module.id}/submit_assessment/',
            {f'question_{self.q1.id}': self.choice_yes.id}
        )
        
        # Verify submission exists and is passed
        sub2 = AssessmentSubmission.objects.filter(user=user, assessment=self.assessment).latest('submitted_at')
        self.assertEqual(sub2.score, 100.0)
        self.assertTrue(sub2.passed)
        # Check module progress is marked completed
        progress_exists_now = ModuleProgress.objects.filter(user=user, module=self.module, completed=True).exists()
        self.assertTrue(progress_exists_now)

    @patch('course.views.PayStack.generate_checkout_url')
    @patch('course.views.PayStack.verify_payment')
    def test_paid_course_enrollment_flow(self, mock_verify, mock_generate):
        # Set up mock return values before requests are made
        mock_generate.return_value = "https://checkout.paystack.com/mock-url"

        # 1. Create a paid course
        paid_course = Course.objects.create(
            title="Paid Advanced Leadership",
            description="Deep dive paid course.",
            is_paid=True,
            price=5000
        )
        
        # Create user profile to match mentor
        user = User.objects.create_user(username="paid_student@example.com", email="paid_student@example.com")
        UserProfile.objects.create(user=user, gender="M", interests="SPIRITUAL")
        self.client.force_login(user)
        
        # 2. Try to enroll -> should redirect to initiate_payment (which itself redirects with 302)
        response = self.client.post(f'/courses/{paid_course.id}/enroll/')
        self.assertRedirects(response, f'/courses/{paid_course.id}/payment/initiate/', target_status_code=302)
        
        # Verify a pending CoursePayment record is created
        payment_record = CoursePayment.objects.get(user=user, course=paid_course)
        self.assertEqual(payment_record.amount, 5000)
        self.assertFalse(payment_record.approved)
        
        # 3. Access initiate payment view to verify the external Paystack redirect
        response = self.client.get(f'/courses/{paid_course.id}/payment/initiate/')
        self.assertRedirects(response, "https://checkout.paystack.com/mock-url", fetch_redirect_response=False)
        
        # 4. Verify payment callback
        mock_verify.return_value = {
            'status': 'success',
            'metadata': {
                'transaction_type': 'course_payment',
                'course_payment_id': payment_record.id
            }
        }
        
        # Trigger verification
        response = self.client.get('/courses/payment/verify/?reference=mock_reference')
        self.assertRedirects(response, '/courses/dashboard/')
        
        # Check payment record is approved and enrollment is created
        payment_record.refresh_from_db()
        self.assertTrue(payment_record.approved)
        
        enrollment = CourseEnrollment.objects.get(user=user, course=paid_course)
        self.assertIsNotNone(enrollment)
        # Should be matched with male spiritual mentor (Brother John)
        self.assertEqual(enrollment.mentor, self.mentor_male_spiritual)

    def test_certificate_unlocked_on_course_completion(self):
        # 1. Create a 2-module course
        course = Course.objects.create(
            title="Spiritual Warfare Mastery",
            description="Deep understanding of spiritual warfare."
        )
        mod1 = Module.objects.create(
            course=course,
            title="Module 1: Principles",
            order=1,
            content="Module 1 Content"
        )
        mod2 = Module.objects.create(
            course=course,
            title="Module 2: Practical Application",
            order=2,
            content="Module 2 Content"
        )
        # mod2 has an assessment
        assess2 = Assessment.objects.create(
            module=mod2,
            title="Final Assessment",
            passing_score=80
        )
        q = AssessmentQuestion.objects.create(
            assessment=assess2,
            question_text="Are we victorious?",
            question_type="MCQ"
        )
        correct_choice = AssessmentChoice.objects.create(
            question=q,
            choice_text="Yes, through Christ",
            is_correct=True
        )

        user = User.objects.create_user(
            username="completer@example.com",
            email="completer@example.com",
            first_name="Grace",
            last_name="Faith"
        )
        UserProfile.objects.create(user=user, gender="F", interests="SPIRITUAL")
        CourseEnrollment.objects.create(user=user, course=course)
        self.client.force_login(user)

        # Complete Module 1 (non-assessment)
        resp1 = self.client.post(f'/courses/{course.id}/modules/{mod1.id}/complete/')
        # Should redirect to next module because module 2 is not completed
        self.assertRedirects(resp1, f'/courses/{course.id}/modules/{mod2.id}/')
        
        # Verify certificate is NOT unlocked yet
        self.assertFalse(Certificate.objects.filter(user=user, course=course).exists())

        # Complete Module 2 by passing the assessment
        resp2 = self.client.post(
            f'/courses/{course.id}/modules/{mod2.id}/submit_assessment/',
            {f'question_{q.id}': correct_choice.id}
        )
        # Should redirect to certificate detail since all modules are now completed!
        self.assertRedirects(resp2, f'/courses/{course.id}/certificate/')

        # Verify certificate is unlocked
        cert = Certificate.objects.filter(user=user, course=course).first()
        self.assertIsNotNone(cert)
        self.assertTrue(cert.certificate_code.startswith("CAN-"))

        # Access certificate view as the owner
        cert_view_resp = self.client.get(f'/courses/{course.id}/certificate/')
        self.assertEqual(cert_view_resp.status_code, 200)
        self.assertContains(cert_view_resp, "Grace Faith")
        self.assertContains(cert_view_resp, "Spiritual Warfare Mastery")
        self.assertContains(cert_view_resp, cert.certificate_code)

        # Public verification view
        verify_resp = self.client.get(f'/courses/certificate/verify/{cert.certificate_code}/')
        self.assertEqual(verify_resp.status_code, 200)
        self.assertContains(verify_resp, "Grace Faith")
        self.assertContains(verify_resp, "Authenticated Credential")

        # Dashboard shows unlocked certificate and certificate section
        dash_resp = self.client.get('/courses/dashboard/')
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, "Certificate Unlocked")
        self.assertContains(dash_resp, "My Earned Certificates")

    def test_certificate_locked_for_uncompleted_user(self):
        course = Course.objects.create(
            title="Basic Theology",
            description="Foundation of Faith."
        )
        Module.objects.create(
            course=course,
            title="Module 1: Theology 101",
            order=1,
            content="Content"
        )

        user = User.objects.create_user(username="incomplete@example.com", email="incomplete@example.com")
        UserProfile.objects.create(user=user, gender="M", interests="SPIRITUAL")
        CourseEnrollment.objects.create(user=user, course=course)
        self.client.force_login(user)

        # User has NOT completed module 1
        resp = self.client.get(f'/courses/{course.id}/certificate/')
        # Should redirect to course detail with warning message
        self.assertRedirects(resp, f'/courses/{course.id}/')
        self.assertFalse(Certificate.objects.filter(user=user, course=course).exists())

