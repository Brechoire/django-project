from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("project/", include("django_project_manager.urls")),
    path("", RedirectView.as_view(pattern_name="django_project_manager:board", permanent=False)),
]
