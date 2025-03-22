from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from monitor.models import Repository
from monitor.services.github.events import GitHubEventService as GHService


class Command(BaseCommand):
    """
    Management command to fetch recent GitHub events for all active repositories.
    Applies rolling window logic: last N days or last N events per type/repo.
    """

    help = "Fetch GitHub events for active repositories (rolling window: 7 days or 500 events)"

    def __init__(self):
        super().__init__()
        self.page_limit = 10
        self.min_date = now() - timedelta(days=settings.EVENT_DAYS_LIMIT)
        self.event_limit = settings.EVENT_FETCH_LIMIT

    def handle(self, *args, **options):
        """
        Entry point for the management command.
        """
        active_repos = Repository.objects.filter(active=True)
        if not active_repos.exists():
            self.stdout.write("No active repositories found.")
            return

        for repo in active_repos:
            self.stdout.write(f"Fetching events for: {repo.name}")

            result: GHService.EventFetchResult = GHService.fetch_events_for_repository(
                repo, self.page_limit, self.min_date, self.event_limit
            )

            self.stdout.write(
                f"✓ {result['new_events']} new events saved for {repo.name}, "
                f"{result['skipped_events']} known events across {result['pages_fetched']} pages"
            )
