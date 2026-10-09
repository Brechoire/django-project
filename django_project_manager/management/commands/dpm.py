import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_project_manager import services
from django_project_manager.models import Task


class Command(BaseCommand):
    help = "Protocole JSON v1 pour agents IA. Utiliser --actor COMPTE avant l’action."

    def add_arguments(self, parser):
        parser.add_argument("--actor", required=True, help="Identifiant d’un utilisateur Django actif")
        commands = parser.add_subparsers(dest="action", required=True)
        listing = commands.add_parser("list", help="Lister les tâches")
        listing.add_argument("--remaining", action="store_true")
        listing.add_argument("--archived", action="store_true")
        for action in (
            "show",
            "update",
            "subtask",
            "toggle",
            "verify",
            "test",
            "archive",
            "restore",
            "delete",
        ):
            p = commands.add_parser(action)
            p.add_argument("id", type=int)
            if action == "update":
                group = p.add_mutually_exclusive_group(required=True)
                group.add_argument("--data")
                group.add_argument("--file")
            if action == "subtask":
                p.add_argument("--title", required=True)
            if action == "toggle":
                p.add_argument("--subtask-id", required=True, type=int)
            if action == "verify":
                p.add_argument("--notes", required=True)
            if action == "test":
                p.add_argument("--command", required=True)
                p.add_argument("--result", choices=["passed", "failed", "skipped"], required=True)
                p.add_argument("--notes", default="")
            if action == "delete":
                p.add_argument("--confirm", action="store_true")
        for action in ("create", "plan"):
            p = commands.add_parser(action)
            group = p.add_mutually_exclusive_group(required=True)
            group.add_argument("--data")
            group.add_argument("--file")
        agents = commands.add_parser("agents", help="Générer AGENTS.md, sans secret")
        agents.add_argument("--path", default="AGENTS.md")
        agents.add_argument("--overwrite", action="store_true", help="Confirmation explicite du remplacement")

    def output(self, data=None, errors=None):
        self.stdout.write(
            json.dumps(
                {"schema_version": 1, "ok": errors is None, "data": data, "errors": errors or []},
                # ASCII est un sous-ensemble UTF-8 et reste sûr lors d’une redirection
                # depuis une ancienne console Windows ; json.loads restitue les accents.
                ensure_ascii=True,
                default=str,
            )
        )

    def payload(self, options):
        if options.get("file"):
            path = Path(options["file"])
            if path.stat().st_size > 1_000_000:
                raise ValidationError("Le fichier JSON dépasse 1 Mo.")
            content = path.read_text(encoding="utf-8-sig")
        else:
            content = options["data"]
        if len(content) > 1_000_000:
            raise ValidationError("Le JSON dépasse 1 Mo.")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValidationError("Le JSON doit être un objet.")
        for key, value in data.items():
            if key == "tasks":
                continue
            if value is not None and not isinstance(value, str):
                raise ValidationError(f"Le champ {key} doit être une chaîne.")
            if value is None and key != "due_date":
                raise ValidationError(f"Le champ {key} ne peut pas être null.")
        return data

    def handle(self, *args, **options):
        try:
            user_model = get_user_model()
            actor = user_model._default_manager.get(**{user_model.USERNAME_FIELD: options["actor"]})
            if not actor.is_active:
                raise ValidationError("Compte inactif.")
            action = options["action"]
            permissions = ["view_task"]
            if action in ("create", "plan"):
                permissions.append("add_task")
            if action in ("update", "subtask", "toggle", "verify", "test", "archive", "restore"):
                permissions.append("change_task")
            permissions.extend(
                {
                    "subtask": ["add_subtask"],
                    "toggle": ["change_subtask"],
                    "test": ["add_testrun"],
                    "delete": ["delete_task"],
                }.get(action, [])
            )
            if not all(actor.has_perm(f"django_project_manager.{p}") for p in permissions):
                raise ValidationError("Permissions insuffisantes pour cette action.")
            if action == "agents":
                path = Path(options["path"])
                text = self.agents_text()
                try:
                    with path.open("w" if options["overwrite"] else "x", encoding="utf-8") as stream:
                        stream.write(text)
                except FileExistsError:
                    raise ValidationError(
                        "AGENTS.md existe déjà. Fusionnez manuellement ou confirmez avec --overwrite."
                    )
                self.output({"path": str(path)})
                return
            if action == "list":
                tasks = Task.objects.filter(archived=options["archived"]).prefetch_related(
                    "subtasks", "test_runs"
                )
                if options["remaining"]:
                    tasks = tasks.exclude(status="done")
                self.output({"tasks": [services.serialize_task(task) for task in tasks]})
                return
            if action == "plan":
                payload = self.payload(options)
                if (
                    set(payload) != {"tasks"}
                    or not isinstance(payload["tasks"], list)
                    or not 1 <= len(payload["tasks"]) <= 200
                ):
                    raise ValidationError("Un plan contient uniquement tasks, une liste de 1 à 200 tâches.")
                created = []
                with transaction.atomic():
                    for original in payload["tasks"]:
                        if not isinstance(original, dict):
                            raise ValidationError("Chaque tâche doit être un objet.")
                        data = dict(original)
                        subtasks = data.pop("subtasks", [])
                        if (
                            not isinstance(subtasks, list)
                            or len(subtasks) > 100
                            or not all(isinstance(s, str) for s in subtasks)
                        ):
                            raise ValidationError("subtasks doit être une liste de titres (100 maximum).")
                        self.check_fields(data)
                        task = services.create_task(data, actor)
                        for title in subtasks:
                            services.add_subtask(task.pk, title, actor)
                        task.refresh_from_db()
                        created.append(services.serialize_task(task))
                self.output({"tasks": created})
                return
            if action == "create":
                data = self.payload(options)
                self.check_fields(data)
                task = services.create_task(data, actor)
            else:
                pk = options["id"]
                task = Task.objects.get(pk=pk)
                if action == "update":
                    data = self.payload(options)
                    self.check_fields(data)
                    task = services.update_task(pk, data, actor)
                elif action == "subtask":
                    services.add_subtask(pk, options["title"], actor)
                elif action == "toggle":
                    services.toggle_subtask(pk, options["subtask_id"], actor)
                elif action == "verify":
                    services.verify_task(pk, options["notes"], actor)
                elif action == "test":
                    services.record_test(pk, options["command"], options["result"], options["notes"], actor)
                elif action in ("archive", "restore"):
                    task = services.archive_task(pk, actor, action == "archive")
                elif action == "delete":
                    if not options["confirm"]:
                        raise ValidationError("La suppression exige --confirm. Préférez archive.")
                    services.delete_task(pk, actor)
                    self.output({"deleted_id": pk})
                    return
            task.refresh_from_db()
            self.output({"task": services.serialize_task(task)})
        except (
            ValidationError,
            ValueError,
            TypeError,
            OSError,
            user_model.DoesNotExist,
            Task.DoesNotExist,
        ) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            self.output(errors=errors)
            raise CommandError("Action refusée (voir la réponse JSON).") from exc
        except Exception as exc:
            from django_project_manager.models import Subtask

            if isinstance(exc, Subtask.DoesNotExist):
                self.output(errors=["Sous-tâche introuvable dans cette tâche."])
                raise CommandError("Sous-tâche introuvable.") from exc
            raise

    def check_fields(self, data):
        for key, value in data.items():
            if key not in services.EDITABLE:
                raise ValidationError(f"Champ inconnu : {key}")
            if not isinstance(value, str) and not (key == "due_date" and value is None):
                raise ValidationError(f"Type incorrect pour {key}.")

    def agents_text(self):
        # Pas de clé, token, mot de passe, chemin local ou configuration de base de données.
        return """# Coordination du développement — Django Project Manager

Le tableau de bord est accessible sur /project/. Utiliser l’environnement Python du projet.
Les commandes rendent un objet JSON UTF-8 : schema_version=1, ok, data, errors.
Remplacer COMPTE par un utilisateur Django actif doté des permissions nécessaires.
L’accès au terminal et à la base est un accès de confiance ; --actor fournit l’identité
du journal et vérifie les permissions, mais ne constitue pas une authentification réseau.

## Début de session
python manage.py dpm --actor COMPTE list --remaining
python manage.py dpm --actor COMPTE show 1

## Plan et progression
Écrire un fichier plan.json : {"tasks": [{"title": "Exemple", "acceptance_criteria":
"Décrire un comportement vérifiable", "subtasks": ["Implémenter", "Vérifier"]}]}.
python manage.py dpm --actor COMPTE plan --file plan.json
Écrire update.json : {"status": "doing"}.
python manage.py dpm --actor COMPTE update 1 --file update.json
Consigner les références Git avec le champ commits et résumer les changements dans description.

## Clôture obligatoire
1. Exécuter et vérifier les critères d’acceptation, ne pas seulement écrire le code.
2. Cocher chaque sous-tâche vérifiée avec toggle ID --subtask-id ID.
3. Enregistrer les preuves : verify ID --notes "Critères contrôlés et résultats".
4. Exécuter les tests applicables, puis enregistrer leur résultat réel :
   test ID --command "python manage.py test" --result passed --notes "Résultat observé".
   Si aucun test n’est applicable, utiliser skipped avec une justification précise.
   La bibliothèque ne lance pas les commandes ; ne jamais inventer leur résultat.
5. Écrire done.json : {"status": "done"}, puis update ID --file done.json.
Toute modification fonctionnelle invalide la preuve et exige une nouvelle vérification.
Ne jamais inclure de secrets dans les tâches, notes ou fichiers générés.

## Fin et reprise
Consigner le bilan dans Sessions IA sur le tableau de bord. Lister les tâches restantes.
Pour archiver : archive ID ; pour restaurer : restore ID. La suppression est irréversible.
Pour les détails du protocole, consulter docs/integration-ia.md et les schémas JSON du paquet.
"""
