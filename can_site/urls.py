
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
