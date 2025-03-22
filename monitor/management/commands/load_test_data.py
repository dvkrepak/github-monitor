from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from monitor.models import Repository, EventType, Event


class Command(BaseCommand):
    help = "Load test repositories, event types, and events"

    def handle(self, *args, **options):
        self.stdout.write("Creating test data...")

        # Active repositories
        active_repos = [
            ("django/django", 4164482),
            ("psf/requests", 1362490),
            ("pallets/flask", 595535),
            ("tiangolo/fastapi", 197493803),
            ("encode/django-rest-framework", 1199691),
        ]

        # Inactive repositories
        inactive_repos = [
            ("torvalds/linux", 2325298),
            ("apple/swift", 44838949),
            ("microsoft/vscode", 41881900),
        ]

        # Example of event types
        event_types = ["PushEvent", "PullRequestEvent", "IssuesEvent"]

        # Create repositories
        for name, repo_id in active_repos:
            Repository.objects.get_or_create(name=name, gh_repo_id=repo_id, active=True)

        for name, repo_id in inactive_repos:
            Repository.objects.get_or_create(name=name, gh_repo_id=repo_id, active=False)

        # Create event types
        for etype in event_types:
            EventType.objects.get_or_create(event_type=etype)

        # Create events only for active repositories
        for repo in Repository.objects.filter(active=True):
            for etype in EventType.objects.all():
                self._create_random_events(repo, etype)

        self.stdout.write(self.style.SUCCESS("✓ Test data loaded."))

    @staticmethod
    def _create_random_events(repo, event_type):
        """
        Create random events within the past 7 days for a given (repo, event_type).
        """
        now = timezone.now()
        num_events = random.randint(50, 150)

        for _ in range(num_events):
            delta = timedelta(minutes=random.randint(0, 60 * 24 * 7))
            created_at = now - delta

            # Ensure uniqueness per (repo, type, timestamp)
            if not Event.objects.filter(repo=repo, event_type=event_type, created_at=created_at).exists():
                Event.objects.create(
                    repo=repo,
                    event_type=event_type,
                    created_at=created_at
                )
