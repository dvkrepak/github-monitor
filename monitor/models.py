from django.core.exceptions import ValidationError
from django.db import models

class Repository(models.Model):
    """
    GitHub repository being monitored.
    """
    name = models.CharField(max_length=255, unique=True)  # e.g. "octocat/Hello-World"
    gh_repo_id = models.BigIntegerField(unique=True)
    active = models.BooleanField(default=True)

    def clean(self):
        # The application can monitor up to five configurable repositories.
        if not self.pk:  # Instance creation
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
    Distinct GitHub event types (e.g. PushEvent, PullRequestEvent).
    """
    event_type = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.event_type

    class Meta:
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'


class Event(models.Model):
    """
    GitHub Event instance, linked to repository and type.
    Stores GitHub's original timestamp (not time of saving).
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
