
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from cicd.views import deploy

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include('main.urls')),
    path("", include('user_authentication.urls')),
    path("publications/", include('publication.urls')),
    path("courses/", include('course.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
    path("deploy/", deploy),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
