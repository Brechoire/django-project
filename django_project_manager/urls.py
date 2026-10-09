from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from . import views

app_name = "django_project_manager"
urlpatterns = [
    path("", views.board, name="board"),
    path(
        "connexion/",
        views.FrenchLoginView.as_view(
            template_name="django_project_manager/login.html",
            next_page=reverse_lazy("django_project_manager:board"),
        ),
        name="login",
    ),
    path(
        "deconnexion/",
        LogoutView.as_view(next_page=reverse_lazy("django_project_manager:login")),
        name="logout",
    ),
    path("taches/nouvelle/", views.task_create, name="task_create"),
    path("taches/<int:pk>/", views.task_detail, name="task_detail"),
    path("taches/<int:pk>/modifier/", views.task_edit, name="task_edit"),
    path("taches/<int:pk>/supprimer/", views.task_delete, name="task_delete"),
    path("taches/<int:pk>/actions/<str:action>/", views.task_action, name="task_action"),
    path("journal/", views.history, name="history"),
    path("tests/", views.tests, name="tests"),
    path("notes/", views.notes, name="notes"),
    path("sessions/", views.sessions, name="sessions"),
    path("sessions/<int:pk>/cloturer/", views.close_session, name="close_session"),
    path("statistiques/", views.stats, name="stats"),
]
