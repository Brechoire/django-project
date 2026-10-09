from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_project_manager import services
from django_project_manager.models import Task


class Command(BaseCommand):
    help = "Créer des exemples dans une base vide, sans créer de compte ni de mot de passe."

    def add_arguments(self, parser):
        parser.add_argument("--actor", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        model = get_user_model()
        try:
            user = model._default_manager.get(**{model.USERNAME_FIELD: options["actor"]})
        except model.DoesNotExist as exc:
            raise CommandError("Créez d’abord votre compte avec createsuperuser.") from exc
        if not user.is_active or not user.is_superuser:
            raise CommandError("La démonstration exige un superutilisateur actif.")
        if Task.objects.exists():
            raise CommandError("La base contient déjà des tâches : aucune donnée ajoutée.")
        examples = [
            (
                "Concevoir l’espace de travail",
                "feature",
                "high",
                "done",
                "Vérifier la navigation au clavier et sur mobile.",
            ),
            (
                "Connecter les agents au projet",
                "feature",
                "high",
                "doing",
                "Les commandes JSON créent et consultent un plan.",
            ),
            (
                "Vérifier les permissions",
                "security",
                "critical",
                "todo",
                "Un lecteur ne peut pas modifier une tâche.",
            ),
            (
                "Documenter la première installation",
                "docs",
                "normal",
                "todo",
                "Le guide fonctionne sur PowerShell et Linux.",
            ),
            (
                "Corriger l’affichage des échéances",
                "bug",
                "high",
                "waiting",
                "Une date vide ne génère pas d’erreur.",
            ),
            (
                "Mesurer les requêtes du Kanban",
                "optimization",
                "low",
                "todo",
                "Mesurer sur un jeu de 100 tâches.",
            ),
            (
                "Tester les transitions de statut",
                "test",
                "normal",
                "doing",
                "La clôture sans preuve est refusée.",
            ),
        ]
        for title, category, priority, status, criteria in examples:
            task = services.create_task(
                {
                    "title": title,
                    "category": category,
                    "priority": priority,
                    "acceptance_criteria": criteria,
                    "description": "Exemple fictif pour découvrir Django Project Manager.",
                },
                user,
            )
            if status == "done":
                services.verify_task(task.pk, "Exemple fictif : validation de démonstration.", user)
                services.record_test(
                    task.pk,
                    "Démonstration fictive",
                    "skipped",
                    "Donnée d’exemple, aucun code livré par cette tâche.",
                    user,
                )
            if status != "todo":
                services.update_task(task.pk, {"status": status}, user)
        self.stdout.write(self.style.SUCCESS("7 tâches d’exemple créées."))
