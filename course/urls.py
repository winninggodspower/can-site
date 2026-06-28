from django.urls import path
from . import views

app_name = 'course'

urlpatterns = [
    path('', views.course_list_view, name='course_list'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_view, name='enroll'),
    path('<int:course_id>/modules/<int:module_id>/', views.module_view, name='module_detail'),
    path('<int:course_id>/modules/<int:module_id>/complete/', views.complete_module_view, name='complete_module'),
    path('<int:course_id>/modules/<int:module_id>/submit_assessment/', views.submit_assessment_view, name='submit_assessment'),
]
