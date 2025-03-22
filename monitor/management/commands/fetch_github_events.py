import requests
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, make_aware

from monitor.models import Repository, Event, EventType
from django.conf import settings


def _save_event(repo, event_type_obj, created_at):
    Event.objects.create(
        repo=repo,
        event_type=event_type_obj,
        created_at=created_at
    )


def _get_or_create_event_type(event_type_str):
    event_type_obj, _ = EventType.objects.get_or_create(event_type=event_type_str)
    return event_type_obj


class Command(BaseCommand):
    help = "Fetch recent GitHub events for active repositories (rolling window: 7 days or 500 events)"

    def __init__(self):
        super().__init__()
        self.token = getattr(settings, 'GITHUB_TOKEN', None)
        self.headers = self.build_headers()
        self.event_limit = int(getattr(settings, "EVENT_FETCH_LIMIT", 500))

        self.min_date = now() - timedelta(days=int(getattr(settings, "EVENT_FETCH_DAYS", 7)))
        self.page_limit = 10

        active_repos = Repository.objects.filter(active=True)
        if not active_repos.exists():
            self.stdout.write("No active repositories found.")
            return

        for repo in active_repos:
            self.fetch_events_for_repository(repo)

    def build_headers(self):
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_events_for_repository(self, repo):
        self.stdout.write(f"\nFetching events for: {repo.name}")
        base_url = f"https://api.github.com/repos/{repo.name}/events"
        new_events = 0
        page = 1

        while page <= self.page_limit:
            url = f"{base_url}?per_page=100&page={page}"
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                self.stderr.write(
                    f"Failed to fetch events for {repo.name} (page {page}). Status code: {response.status_code}")
                break

            events_data = response.json()
            if not events_data:
                break

            should_stop, added = self.process_events(events_data, repo)
            new_events += added

            if should_stop:
                break

            page += 1

        self.stdout.write(f"✓ {new_events} new events saved for {repo.name}")

    def process_events(self, events_data, repo):
        added = 0
        for event_json in events_data:
            event_type_str = event_json.get("type")
            created_at_str = event_json.get("created_at")

            if not event_type_str or not created_at_str:
                continue

            created_at = make_aware(parse_datetime(created_at_str))

            # Stop if event is too old
            if created_at < self.min_date:
                return True, added

            # Skip if already exists
            if Event.objects.filter(
                    repo=repo,
                    event_type__event_type=event_type_str,
                    created_at=created_at
            ).exists():
                continue

            event_type_obj = _get_or_create_event_type(event_type_str)

            if self.reached_event_limit(repo, event_type_obj):
                return True, added

            _save_event(repo, event_type_obj, created_at)
            added += 1

        return False, added

    def reached_event_limit(self, repo, event_type_obj):
        return Event.objects.filter(repo=repo, event_type=event_type_obj).count() >= self.event_limit
