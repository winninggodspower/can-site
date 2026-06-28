from django.test import TestCase
from django.contrib.auth.models import User
from user_authentication.models import UserProfile
from user_authentication.forms import RegisterForm
from course.models import (
    Mentor, Course, Module, Assessment,
    AssessmentQuestion, AssessmentChoice,
    CourseEnrollment, ModuleProgress, AssessmentSubmission
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
