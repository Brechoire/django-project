from django import forms

from .models import AISession, Note, Task, TestRun


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "category",
            "priority",
            "acceptance_criteria",
            "due_date",
            "commits",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "acceptance_criteria": forms.Textarea(attrs={"rows": 3}),
            "commits": forms.Textarea(attrs={"rows": 2}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class TestForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = ["command", "result", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 5})}


class SessionForm(forms.ModelForm):
    class Meta:
        model = AISession
        fields = ["agent", "objective", "summary"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 3})}
