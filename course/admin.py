from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import (
    Mentor, Course, Module, Assessment,
    AssessmentQuestion, AssessmentChoice,
    CourseEnrollment, ModuleProgress, AssessmentSubmission
)

class AssessmentChoiceInline(TabularInline):
    model = AssessmentChoice
    extra = 4

class AssessmentQuestionAdmin(ModelAdmin):
    list_display = ('question_text', 'assessment', 'question_type')
    list_filter = ('assessment', 'question_type')
    inlines = [AssessmentChoiceInline]

class AssessmentQuestionInline(StackedInline):
    model = AssessmentQuestion
    extra = 1
    show_change_link = True

class AssessmentAdmin(ModelAdmin):
    list_display = ('title', 'module', 'passing_score')
    inlines = [AssessmentQuestionInline]

class ModuleInline(StackedInline):
    model = Module
    extra = 1
    show_change_link = True
    fields = ('title', 'order', 'youtube_link', 'content')
    class Media:
        js = (
            'https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js',
            'js/admin_ckeditor.js',
        )

class CourseAdmin(ModelAdmin):
    list_display = ('title', 'created_at')
    inlines = [ModuleInline]
    class Media:
        js = (
            'https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js',
            'js/admin_ckeditor.js',
        )

class ModuleAdmin(ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    class Media:
        js = (
            'https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js',
            'js/admin_ckeditor.js',
        )

class MentorAdmin(ModelAdmin):
    list_display = ('name', 'email', 'gender', 'expertise', 'max_mentees')
    list_filter = ('gender', 'expertise')

class CourseEnrollmentAdmin(ModelAdmin):
    list_display = ('user', 'course', 'mentor', 'enrolled_at')
    list_filter = ('course', 'mentor')

class ModuleProgressAdmin(ModelAdmin):
    list_display = ('user', 'module', 'completed', 'completed_at')
    list_filter = ('completed', 'module__course')

class AssessmentSubmissionAdmin(ModelAdmin):
    list_display = ('user', 'assessment', 'score', 'passed', 'submitted_at')
    list_filter = ('passed', 'assessment__module__course')

admin.site.register(Mentor, MentorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(AssessmentQuestion, AssessmentQuestionAdmin)
admin.site.register(CourseEnrollment, CourseEnrollmentAdmin)
admin.site.register(ModuleProgress, ModuleProgressAdmin)
admin.site.register(AssessmentSubmission, AssessmentSubmissionAdmin)

