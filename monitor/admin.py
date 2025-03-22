from django.contrib import admin
from .models import Repository, Event, EventType


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """
    Admin config for Repository model.
    Automatically fetches gh_repo_id from GitHub API if not provided.
    """

    list_display = ("name", "gh_repo_id", "active")
    list_filter = ("active",)
    search_fields = ("name", "gh_repo_id")
    ordering = ("name",)
    readonly_fields = ("gh_repo_id",)

    def save_model(self, request, obj, form, change):
        """
        Auto-fill gh_repo_id using GitHub API based on 'name' if not set manually.
        """
        if not obj.gh_repo_id:
            import requests
            headers = {"Accept": "application/vnd.github+json"}
            from django.conf import settings
            token = getattr(settings, 'GITHUB_TOKEN', None)
            if token:
                headers["Authorization"] = f"Bearer {token}"

            resp = requests.get(f"https://api.github.com/repos/{obj.name}", headers=headers)
            if resp.status_code == 200:
                obj.gh_repo_id = resp.json().get("id")
            else:
                raise Exception(f"Cannot fetch GitHub repo ID for {obj.name}")

        super().save_model(request, obj, form, change)


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    """
    Admin config for EventType model.
    """
    list_display = ("event_type",)
    search_fields = ("event_type",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin config for Event model.
    Allows filtering by repository and event type.
    """
    list_display = ("repo", "event_type", "created_at")
    list_filter = ("event_type", "repo")
    search_fields = ("repo__name", "event_type__event_type")
    ordering = ("-created_at",)
