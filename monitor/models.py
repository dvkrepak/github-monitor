from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

class Repository(models.Model):
    """
    Represents a GitHub repository being monitored.

    Fields:
    - name: Full repository name, e.g. "owner/repo"
    - gh_repo_id: GitHub's internal numeric ID
    - active: Whether the repository is currently monitored
    """
    name = models.CharField(max_length=255, unique=True)  # e.g. "octocat/Hello-World"
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    gh_repo_id = models.BigIntegerField(unique=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        """
        Enforce a maximum of 5 active repositories.
        This is validated on both creation and activation.
        """
        if not self.pk:  # New instance
            if self.active and Repository.objects.filter(active=True).count() >= 5:
                raise ValidationError("Only up to 5 active repositories are allowed.")
        else:  # Instance update
            previous = Repository.objects.get(pk=self.pk)
            if not previous.active and self.active:  # Was not active and now is
                if Repository.objects.filter(active=True).count() >= 5:
                    raise ValidationError("Only up to 5 active repositories are allowed.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'


class EventType(models.Model):
    """
    Represents a distinct GitHub event type.
    Example values: "PushEvent", "PullRequestEvent"
    """
    event_type = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.event_type

    class Meta:
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'


class Event(models.Model):
    """
    Represents a GitHub event for a specific repository and event type.

    Fields:
    - event_type: FK to EventType
    - repo: FK to Repository
    - created_at: Original event timestamp from GitHub
    """
    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT)
    repo = models.ForeignKey(Repository, on_delete=models.PROTECT)
    created_at = models.DateTimeField()  # timestamp from GitHub

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
