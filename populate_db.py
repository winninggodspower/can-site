import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'can_site.settings')
django.setup()

from django.contrib.auth.models import User
from course.models import Mentor, Course, Module, Assessment, AssessmentQuestion, AssessmentChoice

# Create some mentors if they don't exist
m1, _ = Mentor.objects.get_or_create(
    name="Dr. Elizabeth Aden",
    email="elizabeth@example.com",
    gender="F",
    expertise="SPIRITUAL",
    max_mentees=10
)
m2, _ = Mentor.objects.get_or_create(
    name="Pastor Samuel Johnson",
    email="samuel@example.com",
    gender="M",
    expertise="SPIRITUAL",
    max_mentees=10
)
m3, _ = Mentor.objects.get_or_create(
    name="Coach Robert Carter",
    email="robert@example.com",
    gender="M",
    expertise="CAREER",
    max_mentees=10
)
m4, _ = Mentor.objects.get_or_create(
    name="Lady Jennifer Watson",
    email="jennifer@example.com",
    gender="F",
    expertise="LEADERSHIP",
    max_mentees=10
)

# Create some courses
c1, _ = Course.objects.get_or_create(
    title="Foundations of Faith & Spiritual Growth",
    description="This course is designed to take you on a deep spiritual journey. It covers the essentials of personal ministry, spiritual warfare, prayer habits, and understanding the scriptures. By the end of this course, you will be well equipped to lead others in spiritual growth."
)

c2, _ = Course.objects.get_or_create(
    title="Strategic Career Positioning",
    description="A professional course designed to help young leaders find global relevance in their careers. Topics include workplace ethics, building authority in your field, networking, and public speaking."
)

c3, _ = Course.objects.get_or_create(
    title="Advanced Kingdom Leadership Masterclass",
    defaults={
        'description': "A premium self-paced course designed for ministry and corporate leaders seeking global relevance, advanced team governance, and biblical strategy. Access to exclusive resources and mentorship.",
        'is_paid': True,
        'price': 15000
    }
)

# Create modules for Course 1
mod1, _ = Module.objects.get_or_create(
    course=c1,
    order=1,
    defaults={
        'title': "Module 1: The Devotional Life",
        'youtube_link': "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        'content': """
            <h3>Introduction to Devotional habits</h3>
            <p>A thriving relationship with God is the foundation of all ministry. In this module, we discuss how to build a consistent personal altar, spend quality time in prayer, and study the word of God systematically.</p>
            <h3>Key Principles:</h3>
            <ul>
                <li>Silence and Solitude: Finding a quiet space.</li>
                <li>Systematic Reading: Studying book-by-book rather than random selection.</li>
                <li>Prayer Log: Keeping track of what you pray for.</li>
            </ul>
        """
    }
)

mod2, _ = Module.objects.get_or_create(
    course=c1,
    order=2,
    defaults={
        'title': "Module 2: Servant Leadership Model",
        'youtube_link': "https://www.youtube.com/watch?v=y8Yv4_219E8",
        'content': """
            <h3>Servant Leadership Model</h3>
            <p>Leadership in the Kingdom of God is completely opposite to the secular world's leadership. Here, to lead is to serve. We study the character traits of Moses, David, and Christ Himself.</p>
        """
    }
)

# Create Assessment for Module 1
a1, _ = Assessment.objects.get_or_create(
    module=mod1,
    defaults={
        'title': "Devotional Life Quiz",
        'passing_score': 100
    }
)

# Questions
q1, _ = AssessmentQuestion.objects.get_or_create(
    assessment=a1,
    question_text="What is the foundation of a thriving ministry?",
    question_type="MCQ"
)
AssessmentChoice.objects.get_or_create(question=q1, choice_text="Public speaking ability", is_correct=False)
AssessmentChoice.objects.get_or_create(question=q1, choice_text="A thriving personal relationship with God", is_correct=True)
AssessmentChoice.objects.get_or_create(question=q1, choice_text="High educational qualifications", is_correct=False)
AssessmentChoice.objects.get_or_create(question=q1, choice_text="Wealth and physical resources", is_correct=False)

q2, _ = AssessmentQuestion.objects.get_or_create(
    assessment=a1,
    question_text="Name one system discussed for systematic bible reading.",
    question_type="TEXT"
)

print("Database successfully populated with demo course data!")
