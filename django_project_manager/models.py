from django.conf import settings
from django.db import models


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "À faire"
        DOING = "doing", "En cours"
        WAITING = "waiting", "En attente"
        DONE = "done", "Terminé"

    class Category(models.TextChoices):
        FEATURE = "feature", "Fonctionnalité"
        BUG = "bug", "Bug"
        OPTIMIZATION = "optimization", "Optimisation"
        SECURITY = "security", "Sécurité"
        DOCS = "docs", "Documentation"
        TEST = "test", "Test"

    class Priority(models.TextChoices):
        LOW = "low", "Faible"
        NORMAL = "normal", "Normale"
        HIGH = "high", "Haute"
        CRITICAL = "critical", "Critique"

    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    category = models.CharField(
        "Catégorie", max_length=20, choices=Category.choices, default=Category.FEATURE
    )
    priority = models.CharField("Priorité", max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField("Statut", max_length=20, choices=Status.choices, default=Status.TODO)
    acceptance_criteria = models.TextField("Critères d’acceptation", blank=True)
    acceptance_verified = models.BooleanField("Critères vérifiés", default=False)
    verification_notes = models.TextField("Preuves de vérification", blank=True)
    commits = models.TextField("Références Git", blank=True)
    due_date = models.DateField("Échéance", blank=True, null=True)
    archived = models.BooleanField("Archivée", default=False)
    created_at = models.DateTimeField("Création", auto_now_add=True)
    updated_at = models.DateTimeField("Modification", auto_now=True)

    class Meta:
        ordering = ["-updated_at", "pk"]
        verbose_name = "tâche"
        verbose_name_plural = "tâches"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["todo", "doing", "waiting", "done"]), name="dpm_task_status"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    category__in=["feature", "bug", "optimization", "security", "docs", "test"]
                ),
                name="dpm_task_category",
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=["low", "normal", "high", "critical"]),
                name="dpm_task_priority",
            ),
        ]

    def __str__(self):
        return self.title


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField("Sous-tâche", max_length=200)
    done = models.BooleanField("Terminée", default=False)

    class Meta:
        ordering = ["pk"]


class TestRun(models.Model):
    class Result(models.TextChoices):
        PASSED = "passed", "Réussi"
        FAILED = "failed", "Échoué"
        SKIPPED = "skipped", "Non applicable"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="test_runs")
    command = models.CharField("Commande ou contrôle manuel", max_length=500)
    result = models.CharField("Résultat", max_length=20, choices=Result.choices)
    notes = models.TextField("Résultat détaillé / justification", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class Activity(models.Model):
    task = models.ForeignKey(
        Task, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities"
    )
    task_title = models.CharField(max_length=200, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        default_permissions = ("view",)


class AISession(models.Model):
    agent = models.CharField("Agent", max_length=100)
    objective = models.CharField("Objectif", max_length=200)
    summary = models.TextField("Bilan et prochaine étape", blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField("Fin", null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "session IA"


class Note(models.Model):
    title = models.CharField("Titre", max_length=200)
    content = models.TextField("Note ou décision technique")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "note"
