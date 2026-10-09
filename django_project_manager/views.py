from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone, translation
from django.views.decorators.http import require_POST

from . import services
from .forms import NoteForm, SessionForm, TaskForm, TestForm
from .models import Activity, AISession, Note, Task, TestRun


class FrenchLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        with translation.override("fr"):
            response = super().dispatch(request, *args, **kwargs)
            # LoginView renvoie une TemplateResponse différée : rendre avant de
            # restaurer la langue du projet hôte, y compris les libellés paresseux.
            if hasattr(response, "render"):
                response.render()
            return response


def access(permission="view_task"):
    def decorator(view):
        @wraps(view)
        @login_required(login_url=reverse_lazy("django_project_manager:login"))
        @permission_required(f"django_project_manager.{permission}", raise_exception=True)
        @permission_required("django_project_manager.view_task", raise_exception=True)
        def wrapped(*args, **kwargs):
            with translation.override("fr"):
                return view(*args, **kwargs)

        return wrapped

    return decorator


def board_context(request):
    tasks = Task.objects.prefetch_related("subtasks").annotate(
        subtask_count=Count("subtasks"),
        completed_subtask_count=Count("subtasks", filter=Q(subtasks__done=True)),
    )
    archived = request.GET.get("archived") == "1"
    tasks = tasks.filter(archived=archived)
    total = tasks.count()
    done = tasks.filter(status=Task.Status.DONE).count()
    query = request.GET.get("q", "")[:200]
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    for field in ("category", "priority"):
        if request.GET.get(field):
            tasks = tasks.filter(**{field: request.GET[field]})
    return {
        "columns": [
            {"key": key, "label": label, "tasks": list(tasks.filter(status=key))}
            for key, label in Task.Status.choices
        ],
        "total": total,
        "done": done,
        "progress": round(done * 100 / total) if total else 0,
        "doing": Task.objects.filter(archived=archived, status=Task.Status.DOING).count(),
        "categories": Task.Category.choices,
        "priorities": Task.Priority.choices,
        "q": query,
        "category": request.GET.get("category", ""),
        "priority": request.GET.get("priority", ""),
        "archived": archived,
        "section": "board",
    }


@access()
def board(request):
    template = (
        "django_project_manager/board_content.html"
        if request.headers.get("HX-Request")
        else "django_project_manager/board.html"
    )
    return render(request, template, board_context(request))


@access("add_task")
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = services.create_task(form.cleaned_data, request.user)
        messages.success(request, "La tâche a été créée.")
        return redirect("django_project_manager:task_detail", pk=task.pk)
    return render(
        request, "django_project_manager/task_form.html", {"form": form, "heading": "Nouvelle tâche"}
    )


@access()
def task_detail(request, pk):
    task = get_object_or_404(Task.objects.prefetch_related("subtasks", "test_runs", "activities"), pk=pk)
    return render(
        request,
        "django_project_manager/task_detail.html",
        {"task": task, "test_form": TestForm(), "statuses": Task.Status.choices, "section": "board"},
    )


@access("change_task")
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        try:
            services.update_task(pk, form.cleaned_data, request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "La tâche a été mise à jour.")
            return redirect("django_project_manager:task_detail", pk=pk)
    return render(
        request, "django_project_manager/task_form.html", {"form": form, "heading": "Modifier la tâche"}
    )


@require_POST
@access("change_task")
def task_action(request, pk, action):
    get_object_or_404(Task, pk=pk)
    try:
        if action == "move":
            services.update_task(pk, {"status": request.POST.get("status", "")}, request.user)
        elif action == "archive":
            services.archive_task(pk, request.user)
        elif action == "restore":
            services.archive_task(pk, request.user, False)
        elif action == "verify":
            services.verify_task(pk, request.POST.get("notes", ""), request.user)
        elif action == "subtask":
            if not request.user.has_perm("django_project_manager.add_subtask"):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
            services.add_subtask(pk, request.POST.get("title", ""), request.user)
        elif action == "toggle":
            if not request.user.has_perm("django_project_manager.change_subtask"):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
            sub = get_object_or_404(Task.objects.get(pk=pk).subtasks, pk=request.POST.get("subtask_id", "0"))
            services.toggle_subtask(pk, sub.pk, request.user)
        elif action == "test":
            if not request.user.has_perm("django_project_manager.add_testrun"):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
            form = TestForm(request.POST)
            if not form.is_valid():
                raise ValidationError([str(e) for errors in form.errors.values() for e in errors])
            services.record_test(pk, actor=request.user, **form.cleaned_data)
        else:
            return HttpResponseBadRequest("Action inconnue.")
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Modification enregistrée.")
    if request.headers.get("HX-Request"):
        return render(request, "django_project_manager/board_content.html", board_context(request))
    return redirect("django_project_manager:task_detail", pk=pk)


@access("delete_task")
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        services.delete_task(pk, request.user)
        messages.success(request, "La tâche a été supprimée. Son historique est conservé.")
        return redirect("django_project_manager:board")
    return render(request, "django_project_manager/delete.html", {"task": task})


@access("view_activity")
def history(request):
    from django.core.paginator import Paginator

    page = Paginator(Activity.objects.select_related("actor", "task"), 40).get_page(request.GET.get("page"))
    return render(request, "django_project_manager/history.html", {"page": page, "section": "history"})


@access("view_testrun")
def tests(request):
    from django.core.paginator import Paginator

    page = Paginator(TestRun.objects.select_related("task"), 40).get_page(request.GET.get("page"))
    return render(request, "django_project_manager/tests.html", {"page": page, "section": "tests"})


@access("view_note")
def notes(request):
    from django.core.exceptions import PermissionDenied
    from django.core.paginator import Paginator

    form = NoteForm(request.POST or None)
    if request.method == "POST":
        if not request.user.has_perm("django_project_manager.add_note"):
            raise PermissionDenied
        if form.is_valid():
            note = form.save()
            services.log(None, request.user, "Décision consignée", {"titre": note.title})
            return redirect("django_project_manager:notes")
    page = Paginator(Note.objects.all(), 20).get_page(request.GET.get("page"))
    return render(
        request, "django_project_manager/notes.html", {"page": page, "form": form, "section": "notes"}
    )


@access("view_aisession")
def sessions(request):
    from django.core.exceptions import PermissionDenied
    from django.core.paginator import Paginator

    form = SessionForm(request.POST or None)
    if request.method == "POST":
        if not request.user.has_perm("django_project_manager.add_aisession"):
            raise PermissionDenied
        if form.is_valid():
            session = form.save()
            services.log(
                None,
                request.user,
                "Session IA ouverte",
                {"agent": session.agent, "objectif": session.objective},
            )
            return redirect("django_project_manager:sessions")
    page = Paginator(AISession.objects.all(), 20).get_page(request.GET.get("page"))
    return render(
        request, "django_project_manager/sessions.html", {"page": page, "form": form, "section": "sessions"}
    )


@require_POST
@access("change_aisession")
def close_session(request, pk):
    session = get_object_or_404(AISession, pk=pk)
    if not session.ended_at:
        session.ended_at = timezone.now()
        session.summary = request.POST.get("summary", "")
        session.save()
        services.log(
            None, request.user, "Session IA clôturée", {"agent": session.agent, "bilan": session.summary}
        )
    return redirect("django_project_manager:sessions")


@access()
def stats(request):
    tasks = Task.objects.filter(archived=False)
    total = tasks.count()
    return render(
        request,
        "django_project_manager/stats.html",
        {
            "section": "stats",
            "total": total,
            "progress": round(tasks.filter(status="done").count() * 100 / total) if total else 0,
            "statuses": [
                {"label": label, "count": tasks.filter(status=key).count()}
                for key, label in Task.Status.choices
            ],
            "categories": [
                {"label": label, "count": tasks.filter(category=key).count()}
                for key, label in Task.Category.choices
            ],
            "late": tasks.filter(due_date__lt=timezone.localdate()).exclude(status="done").count(),
        },
    )
