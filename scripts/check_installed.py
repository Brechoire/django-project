"""Contrôle d’intégration du wheel : aucun import depuis les sources du dépôt.

À exécuter avec le Python d’un environnement neuf contenant le wheel.
"""

# Les imports dépendant du registre d’applications suivent django.setup().
# ruff: noqa: E402
import json
import sys
from io import StringIO
from pathlib import Path
from types import ModuleType

import django
from django.conf import settings

import django_project_manager

source = Path(__file__).resolve().parent.parent / "django_project_manager"
assert not Path(django_project_manager.__file__).resolve().is_relative_to(source), (
    "Import depuis les sources !"
)
host_urls = ModuleType("dpm_integration_host_urls")
sys.modules[host_urls.__name__] = host_urls
settings.configure(
    SECRET_KEY="integration-check-only",
    ROOT_URLCONF=host_urls.__name__,
    ALLOWED_HOSTS=["testserver"],
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django_project_manager",
    ],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    MIDDLEWARE=[
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        }
    ],
    STATIC_URL="/static/",
    USE_TZ=True,
)
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.template.loader import get_template
from django.test import Client
from django.urls import include, path

host_urls.urlpatterns = [path("project/", include("django_project_manager.urls"))]

call_command("migrate", verbosity=0)
user = get_user_model().objects.create_superuser("integration", "", "integration-only-password")
out = StringIO()
call_command(
    "dpm", "--actor", "integration", "create", "--data", '{"title":"Installation externe"}', stdout=out
)
assert json.loads(out.getvalue())["ok"]
assert get_template("django_project_manager/board.html")
assert finders.find("django_project_manager/app.css")
assert finders.find("django_project_manager/vendor/htmx.min.js")
assert (Path(django_project_manager.__file__).parent / "schemas" / "response-v1.json").exists()
client = Client()
assert client.get("/project/").status_code == 302
client.force_login(user)
response = client.get("/project/")
assert response.status_code == 200
assert "Installation externe" in response.content.decode()
assert client.post("/project/taches/1/actions/move/", {"status": "doing"}).status_code == 302
print(f"Wheel installé et opérationnel sur Django {django.get_version()} : {django_project_manager.__file__}")
