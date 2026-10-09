"""Unique chemin d’écriture pour l’interface et les commandes agents.

Les commandes de tests sont des preuves déclarées : elles ne sont jamais exécutées
par l’application. Seul l’agent ou l’utilisateur les exécute dans son environnement.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Activity, Subtask, Task, TestRun

EDITABLE = {
    "title",
    "description",
    "category",
    "priority",
    "status",
    "acceptance_criteria",
    "commits",
    "due_date",
}
INVALIDATES = {"title", "description", "acceptance_criteria", "commits"}


def log(task, actor, action, details=None):
    Activity.objects.create(
        task=task, task_title=task.title if task else "", actor=actor, action=action, details=details or {}
    )


def invalidate(task):
    task.acceptance_verified = False
    task.verification_notes = ""
    if task.status == Task.Status.DONE:
        task.status = Task.Status.DOING


def require_completion(task):
    errors = []
    if (
        not task.acceptance_criteria.strip()
        or not task.acceptance_verified
        or not task.verification_notes.strip()
    ):
        errors.append("Renseignez les critères d’acceptation et leur preuve de vérification.")
    if task.subtasks.filter(done=False).exists():
        errors.append("Terminez toutes les sous-tâches.")
    last = task.test_runs.first()
    if not last or last.created_at < task.updated_at or last.result == TestRun.Result.FAILED:
        errors.append(
            "Enregistrez un contrôle récent réussi ou non applicable après la dernière modification."
        )
    elif last.result == TestRun.Result.SKIPPED and not last.notes.strip():
        errors.append("Justifiez pourquoi aucun test n’est applicable.")
    if errors:
        raise ValidationError(errors)


@transaction.atomic
def create_task(data, actor):
    unknown = set(data) - EDITABLE
    if unknown:
        raise ValidationError(f"Champs inconnus : {', '.join(sorted(unknown))}")
    task = Task(**data)
    if task.status == Task.Status.DONE:
        raise ValidationError("Créez la tâche puis vérifiez-la avant de la terminer.")
    task.full_clean()
    task.save()
    log(task, actor, "Tâche créée")
    return task


@transaction.atomic
def update_task(pk, data, actor):
    task = Task.objects.select_for_update().get(pk=pk)
    unknown = set(data) - EDITABLE
    if unknown:
        raise ValidationError(f"Champs inconnus : {', '.join(sorted(unknown))}")
    tracked = EDITABLE | {"acceptance_verified", "verification_notes"}
    before = {key: getattr(task, key) for key in tracked}
    for key, value in data.items():
        setattr(task, key, value)
    task.full_clean()
    content_changed = any(before[key] != getattr(task, key) for key in INVALIDATES)
    if content_changed:
        invalidate(task)
        if data.get("status") == Task.Status.DONE:
            task.status = Task.Status.DONE
    if task.status == Task.Status.DONE and (before["status"] != Task.Status.DONE or content_changed):
        require_completion(task)
    changes = {
        key: {"avant": str(before[key]), "après": str(getattr(task, key))}
        for key in tracked
        if before[key] != getattr(task, key)
    }
    if changes:
        task.save()
        log(task, actor, "Tâche modifiée", changes)
    return task


@transaction.atomic
def verify_task(pk, notes, actor):
    task = Task.objects.select_for_update().get(pk=pk)
    if not task.acceptance_criteria.strip() or not notes.strip():
        raise ValidationError("Décrivez les critères et les preuves de vérification.")
    task.acceptance_verified = True
    task.verification_notes = notes.strip()
    task.save()
    log(task, actor, "Critères vérifiés", {"preuve": notes})
    return task


@transaction.atomic
def add_subtask(pk, title, actor):
    task = Task.objects.select_for_update().get(pk=pk)
    subtask = Subtask(task=task, title=title)
    subtask.full_clean()
    subtask.save()
    invalidate(task)
    task.save()
    log(task, actor, "Sous-tâche ajoutée", {"titre": title})
    return subtask


@transaction.atomic
def toggle_subtask(pk, subtask_pk, actor):
    task = Task.objects.select_for_update().get(pk=pk)
    subtask = task.subtasks.get(pk=subtask_pk)
    subtask.done = not subtask.done
    subtask.save()
    invalidate(task)
    task.save()
    log(task, actor, "Sous-tâche modifiée", {"titre": subtask.title, "terminée": subtask.done})
    return subtask


@transaction.atomic
def record_test(pk, command, result, notes, actor):
    task = Task.objects.select_for_update().get(pk=pk)
    if result == TestRun.Result.SKIPPED and not notes.strip():
        raise ValidationError("Justifiez l’absence de tests applicables.")
    run = TestRun(task=task, command=command, result=result, notes=notes)
    run.full_clean()
    # Ne pas modifier updated_at sur un test réussi : il valide la dernière révision.
    if result == TestRun.Result.FAILED:
        invalidate(task)
        task.save()
    run.save()
    log(task, actor, "Contrôle enregistré", {"commande": command, "résultat": result, "notes": notes})
    return run


@transaction.atomic
def archive_task(pk, actor, archived=True):
    task = Task.objects.select_for_update().get(pk=pk)
    task.archived = archived
    task.save()
    log(task, actor, "Tâche archivée" if archived else "Tâche restaurée")
    return task


@transaction.atomic
def delete_task(pk, actor):
    task = Task.objects.select_for_update().get(pk=pk)
    log(task, actor, "Tâche supprimée", {"id": task.pk})
    task.delete()


def serialize_task(task):
    return {
        "id": task.pk,
        "title": task.title,
        "description": task.description,
        "category": task.category,
        "priority": task.priority,
        "status": task.status,
        "acceptance_criteria": task.acceptance_criteria,
        "acceptance_verified": task.acceptance_verified,
        "verification_notes": task.verification_notes,
        "commits": task.commits,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "archived": task.archived,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "subtasks": list(task.subtasks.values("id", "title", "done")),
        "test_runs": [
            {
                "id": r.pk,
                "command": r.command,
                "result": r.result,
                "notes": r.notes,
                "created_at": r.created_at.isoformat(),
            }
            for r in task.test_runs.all()
        ],
    }
