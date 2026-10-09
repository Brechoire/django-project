"""Administration en lecture seule : les mutations passent par les services vérifiés."""

from django.contrib import admin

from .models import Activity, AISession, Note, Subtask, Task, TestRun


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Task)
class TaskAdmin(ReadOnlyAdmin):
    list_display = ("id", "title", "status", "priority", "archived")
    list_filter = ("status", "category", "archived")
    search_fields = ("title", "description")


for model in (Activity, AISession, Note, Subtask, TestRun):
    admin.site.register(model, ReadOnlyAdmin)
