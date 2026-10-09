import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from django_project_manager import services
from django_project_manager.models import Activity, AISession, Note, Task


class WorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            "admin", "admin@example.invalid", "test-only-password"
        )
        self.reader = get_user_model().objects.create_user("lecteur", password="test-only-password")
        self.reader.user_permissions.add(Permission.objects.get(codename="view_task"))
        self.task = services.create_task(
            {"title": "Tester le parcours", "acceptance_criteria": "Un lecteur reste en lecture seule."},
            self.user,
        )

    def url(self, name, *args):
        return reverse(f"django_project_manager:{name}", args=args)

    def ready(self):
        services.verify_task(self.task.pk, "Le lecteur reçoit une réponse 403 en écriture.", self.user)
        services.record_test(self.task.pk, "python manage.py test", "passed", "Contrôles réussis.", self.user)

    def test_anonymous_redirects_to_local_login(self):
        response = self.client.get(self.url("board"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/project/connexion/", response.url)

    def test_french_login_does_not_change_host_language(self):
        with translation.override("en"):
            response = self.client.get(self.url("login"))
            self.assertContains(response, "Nom d’utilisateur")
            self.assertEqual(translation.get_language(), "en")

    def test_reader_can_view_but_cannot_write(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(self.url("board")).status_code, 200)
        response = self.client.post(self.url("task_action", self.task.pk, "move"), {"status": "doing"})
        self.assertEqual(response.status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "todo")
        self.assertEqual(self.client.get(self.url("notes")).status_code, 403)

    def test_user_without_view_permission_is_denied(self):
        user = get_user_model().objects.create_user("sans-acces")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url("board")).status_code, 403)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(
            client.post(self.url("task_action", self.task.pk, "move"), {"status": "doing"}).status_code, 403
        )

    def test_actions_are_post_only(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url("task_action", self.task.pk, "archive")).status_code, 405)

    def test_completion_requires_acceptance_and_test(self):
        with self.assertRaises(ValidationError):
            services.update_task(self.task.pk, {"status": "done"}, self.user)
        self.ready()
        task = services.update_task(self.task.pk, {"status": "done"}, self.user)
        self.assertEqual(task.status, "done")

    def test_incomplete_subtasks_block_completion(self):
        sub = services.add_subtask(self.task.pk, "Contrôler les permissions", self.user)
        self.ready()
        with self.assertRaises(ValidationError):
            services.update_task(self.task.pk, {"status": "done"}, self.user)
        services.toggle_subtask(self.task.pk, sub.pk, self.user)
        self.ready()
        self.assertEqual(services.update_task(self.task.pk, {"status": "done"}, self.user).status, "done")

    def test_changed_content_invalidates_verification(self):
        self.ready()
        services.update_task(self.task.pk, {"status": "done"}, self.user)
        task = services.update_task(self.task.pk, {"description": "Nouveau comportement"}, self.user)
        self.assertFalse(task.acceptance_verified)
        self.assertEqual(task.status, "doing")
        with self.assertRaises(ValidationError):
            services.update_task(self.task.pk, {"status": "done"}, self.user)

    def test_old_test_does_not_validate_new_revision(self):
        self.ready()
        services.update_task(self.task.pk, {"description": "Modification"}, self.user)
        services.verify_task(self.task.pk, "Nouvelle vérification", self.user)
        with self.assertRaises(ValidationError):
            services.update_task(self.task.pk, {"status": "done"}, self.user)

    def test_done_transition_is_idempotent(self):
        self.ready()
        task = services.update_task(self.task.pk, {"status": "done"}, self.user)
        timestamp = task.updated_at
        task = services.update_task(self.task.pk, {"status": "done"}, self.user)
        self.assertEqual(task.updated_at, timestamp)
        self.assertEqual(task.status, "done")

    def test_completed_metadata_can_be_edited_without_reopening(self):
        self.ready()
        services.update_task(self.task.pk, {"status": "done"}, self.user)
        task = services.update_task(self.task.pk, {"priority": "low"}, self.user)
        self.assertEqual(task.status, "done")
        self.assertTrue(task.acceptance_verified)

    def test_failed_test_reopens_done_task(self):
        self.ready()
        services.update_task(self.task.pk, {"status": "done"}, self.user)
        services.record_test(
            self.task.pk, "Contrôle de régression", "failed", "Régression détectée", self.user
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "doing")
        self.assertFalse(self.task.acceptance_verified)

    def test_skipped_requires_reason(self):
        with self.assertRaises(ValidationError):
            services.record_test(self.task.pk, "Aucun test", "skipped", "", self.user)
        services.verify_task(self.task.pk, "Documentation relue", self.user)
        services.record_test(
            self.task.pk, "Relecture", "skipped", "Changement documentaire uniquement.", self.user
        )
        services.update_task(self.task.pk, {"status": "done"}, self.user)

    def test_cannot_create_already_completed_task(self):
        with self.assertRaises(ValidationError):
            services.create_task({"title": "Invalide", "status": "done"}, self.user)

    def test_invalid_status_rolls_back_without_log(self):
        count = Activity.objects.count()
        with self.assertRaises(ValidationError):
            services.update_task(self.task.pk, {"status": "unknown"}, self.user)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "todo")
        self.assertEqual(Activity.objects.count(), count)

    def test_task_form_creates_and_edits_task(self):
        self.client.force_login(self.user)
        payload = {
            "title": "Nouvelle fonctionnalité",
            "description": "Détails",
            "category": "feature",
            "priority": "high",
            "acceptance_criteria": "Vérifier",
            "due_date": "2026-10-15",
            "commits": "abc123",
        }
        response = self.client.post(self.url("task_create"), payload)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title=payload["title"])
        payload["title"] = "Titre modifié"
        self.assertEqual(self.client.post(self.url("task_edit", task.pk), payload).status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, "Titre modifié")

    def test_all_pages_render(self):
        self.client.force_login(self.user)
        for name in ("board", "task_create", "history", "tests", "notes", "sessions", "stats"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(self.url(name)).status_code, 200)
        for name in ("task_detail", "task_edit", "task_delete"):
            self.assertEqual(self.client.get(self.url(name, self.task.pk)).status_code, 200)

    def test_xss_is_escaped_in_full_and_htmx_views(self):
        services.update_task(self.task.pk, {"title": '<script>alert("x")</script>'}, self.user)
        self.client.force_login(self.user)
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            response = self.client.get(self.url("board"), **headers)
            self.assertContains(response, "&lt;script&gt;")
            self.assertNotContains(response, '<script>alert("x")</script>')

    def test_filters_and_archives(self):
        self.client.force_login(self.user)
        services.create_task(
            {"title": "Incident critique", "category": "bug", "priority": "critical"}, self.user
        )
        response = self.client.get(
            self.url("board"), {"category": "bug", "priority": "critical", "q": "Incident"}
        )
        self.assertContains(response, "Incident critique")
        self.assertNotContains(response, self.task.title)
        services.archive_task(self.task.pk, self.user)
        self.assertNotContains(self.client.get(self.url("board")), self.task.title)
        self.assertContains(self.client.get(self.url("board"), {"archived": "1"}), self.task.title)
        services.archive_task(self.task.pk, self.user, False)
        self.assertContains(self.client.get(self.url("board")), self.task.title)

    def test_htmx_move_and_completion_error_are_rendered(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url("task_action", self.task.pk, "move"), {"status": "doing"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "doing")
        response = self.client.post(
            self.url("task_action", self.task.pk, "move"), {"status": "done"}, HTTP_HX_REQUEST="true"
        )
        self.assertContains(response, "Renseignez les critères")
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "doing")

    def test_subtask_cannot_be_changed_through_other_task(self):
        other = services.create_task({"title": "Autre"}, self.user)
        sub = services.add_subtask(other.pk, "Privée", self.user)
        self.client.force_login(self.user)
        response = self.client.post(self.url("task_action", self.task.pk, "toggle"), {"subtask_id": sub.pk})
        self.assertEqual(response.status_code, 404)
        sub.refresh_from_db()
        self.assertFalse(sub.done)

    def test_delete_keeps_journal(self):
        pk = self.task.pk
        services.delete_task(pk, self.user)
        self.assertFalse(Task.objects.filter(pk=pk).exists())
        event = Activity.objects.get(action="Tâche supprimée")
        self.assertIsNone(event.task_id)
        self.assertEqual(event.task_title, "Tester le parcours")

    def test_notes_and_sessions_are_functional(self):
        self.client.force_login(self.user)
        self.client.post(self.url("notes"), {"title": "SQLite", "content": "Simplicité locale."})
        self.assertEqual(Note.objects.count(), 1)
        self.client.post(
            self.url("sessions"), {"agent": "Codex", "objective": "Implémenter", "summary": "Plan"}
        )
        session = AISession.objects.get()
        self.client.post(self.url("close_session", session.pk), {"summary": "Reprendre les tests"})
        session.refresh_from_db()
        self.assertIsNotNone(session.ended_at)
        self.assertEqual(session.summary, "Reprendre les tests")


class CommandTests(TestCase):
    setUp = WorkflowTests.setUp

    def invoke(self, *args):
        out = StringIO()
        call_command("dpm", "--actor", "admin", *args, stdout=out)
        return json.loads(out.getvalue())

    def test_json_create_show_and_list(self):
        data = self.invoke("create", "--data", json.dumps({"title": "Depuis l’agent"}))
        self.assertEqual(data["schema_version"], 1)
        pk = data["data"]["task"]["id"]
        self.assertEqual(self.invoke("show", str(pk))["data"]["task"]["title"], "Depuis l’agent")
        self.assertEqual(len(self.invoke("list", "--remaining")["data"]["tasks"]), 2)

    def test_plan_is_atomic(self):
        count = Task.objects.count()
        with self.assertRaises(CommandError):
            self.invoke(
                "plan", "--data", json.dumps({"tasks": [{"title": "OK"}, {"title": "KO", "status": "done"}]})
            )
        self.assertEqual(Task.objects.count(), count)

    def test_plan_adds_subtasks(self):
        data = self.invoke(
            "plan", "--data", json.dumps({"tasks": [{"title": "Plan", "subtasks": ["Coder", "Tester"]}]})
        )
        self.assertEqual(len(data["data"]["tasks"][0]["subtasks"]), 2)

    def test_command_rejects_reader_write_and_unknown_fields(self):
        with self.assertRaises(CommandError):
            call_command(
                "dpm", "--actor", "lecteur", "create", "--data", '{"title":"Refusé"}', stdout=StringIO()
            )
        with self.assertRaises(CommandError):
            self.invoke("update", str(self.task.pk), "--data", '{"acceptance_verified":true}')

    def test_agents_never_overwrites_without_explicit_flag(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text("Instructions existantes", encoding="utf-8")
            with self.assertRaises(CommandError):
                self.invoke("agents", "--path", str(path))
            self.assertEqual(path.read_text(encoding="utf-8"), "Instructions existantes")
            self.invoke("agents", "--path", str(path), "--overwrite")
            self.assertIn("Clôture obligatoire", path.read_text(encoding="utf-8"))

    def test_json_file_supports_powershell_bom(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "create.json"
            path.write_text('{"title":"Sécurité"}', encoding="utf-8-sig")
            self.assertEqual(self.invoke("create", "--file", str(path))["data"]["task"]["title"], "Sécurité")

    def test_json_error_envelope_and_exit_failure(self):
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("dpm", "--actor", "admin", "create", "--data", "{invalid", stdout=out)
        data = json.loads(out.getvalue())
        self.assertFalse(data["ok"])
        self.assertTrue(data["errors"])

    def test_agent_completion_path(self):
        pk = str(self.task.pk)
        self.invoke("update", pk, "--data", '{"status":"doing"}')
        sub = self.invoke("subtask", pk, "--title", "Vérifier")["data"]["task"]["subtasks"][0]
        self.invoke("toggle", pk, "--subtask-id", str(sub["id"]))
        self.invoke("verify", pk, "--notes", "Permissions contrôlées")
        self.invoke(
            "test", pk, "--command", "Contrôle manuel", "--result", "passed", "--notes", "Résultat vérifié"
        )
        self.assertEqual(
            self.invoke("update", pk, "--data", '{"status":"done"}')["data"]["task"]["status"], "done"
        )
