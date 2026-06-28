from django.contrib import admin
from .models import (
    Mentor, Course, Module, Assessment,
    AssessmentQuestion, AssessmentChoice,
    CourseEnrollment, ModuleProgress, AssessmentSubmission
)

class AssessmentChoiceInline(admin.TabularInline):
    model = AssessmentChoice
    extra = 4

class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'assessment', 'question_type')
    list_filter = ('assessment', 'question_type')
    inlines = [AssessmentChoiceInline]

class AssessmentQuestionInline(admin.StackedInline):
    model = AssessmentQuestion
    extra = 1

class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'passing_score')
    inlines = [AssessmentQuestionInline]

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1
    fields = ('title', 'order', 'youtube_link', 'content')

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    inlines = [ModuleInline]

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    class Media:
        js = (
            'https://cdn.ckeditor.com/4.16.2/standard/ckeditor.js',
            'js/admin_ckeditor.js',
        )

class MentorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'gender', 'expertise', 'max_mentees')
    list_filter = ('gender', 'expertise')

class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'mentor', 'enrolled_at')
    list_filter = ('course', 'mentor')

admin.site.register(Mentor, MentorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(AssessmentQuestion, AssessmentQuestionAdmin)
admin.site.register(CourseEnrollment, CourseEnrollmentAdmin)
admin.site.register(ModuleProgress)
admin.site.register(AssessmentSubmission)
