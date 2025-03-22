from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_aware

from monitor.models import EventType, Event
from monitor.services.github.api import GitHubAPIClient


class GitHubEventService:
    """
    Handles fetching, processing, and storing GitHub events and event types.
    """

    EventFetchResult = dict[str, int]  # Type allias for result of fetching events for a repository.

    @staticmethod
    def fetch_events_for_repository(repo, page_limit, min_date, event_limit) -> EventFetchResult:
        """
        Fetch events from GitHub for a repository within given limits.

        Args:
            repo: Repository instance to fetch events for.
            page_limit (int): Maximum pages to fetch.
            min_date (datetime): Earliest datetime to accept events from.
            event_limit (int): Max number of events to store per (repo, event type).

        Returns:
            dict: Summary of fetching operation (events added, skipped, pages fetched).
        """
        new_events_total, skipped_events_total, page = 0, 0, 1

        while page <= page_limit:
            response = GitHubAPIClient.fetch_repo_events(repo.name, page)

            if response.status_code in {422, 404}:
                break
            if response.status_code != 200:
                raise Exception(f"GitHub API error ({response.status_code})")

            events_data = response.json()
            if not events_data:
                break

            should_stop, added, skipped = GitHubEventService._process_events(
                events_data, repo, min_date, event_limit
            )

            new_events_total += added
            skipped_events_total += skipped

            if should_stop or len(events_data) < 100:
                break

            page += 1

        return {
            "new_events": new_events_total,
            "skipped_events": skipped_events_total,
            "pages_fetched": page
        }

    @staticmethod
    def _process_events(events_data, repo, min_date, event_limit):
        """
        Processes a batch of GitHub events.

        Args:
            events_data (list): List of raw event JSON objects.
            repo: Repository instance.
            min_date (datetime): Earliest allowed event date.
            event_limit (int): Max events per (repo, event type).

        Returns:
            tuple: (should_stop, events_added, events_skipped) flags.
        """
        added, skipped_existing = 0, 0

        for event_json in events_data:
            if GitHubEventService._event_data_invalid(event_json):
                continue

            created_at = GitHubEventService._normalize_datetime(event_json["created_at"])

            if created_at < min_date:
                return True, added, skipped_existing

            event_type_str = event_json["type"]

            if GitHubEventService._event_exists(repo, event_type_str, created_at):
                skipped_existing += 1
                continue

            event_type_obj = GitHubEventService.get_or_create_event_type(event_type_str)

            if GitHubEventService.reached_event_limit(repo, event_type_obj, event_limit):
                return True, added, skipped_existing

            GitHubEventService.save_event(repo, event_type_obj, created_at)
            added += 1

        if added == 0 and skipped_existing == len(events_data):
            return True, added, skipped_existing

        return False, added, skipped_existing

    @staticmethod
    def _normalize_datetime(date_str):
        """Parses and makes aware a datetime string."""
        dt = parse_datetime(date_str)
        return make_aware(dt) if dt and not is_aware(dt) else dt

    @staticmethod
    def _event_exists(repo, event_type_str, created_at):
        """Checks if event already exists."""
        return Event.objects.filter(
            repo=repo,
            event_type__event_type=event_type_str,
            created_at=created_at
        ).exists()

    @staticmethod
    def _event_data_invalid(event_json):
        """Checks if event data lacks required fields."""
        return not event_json.get("type") or not event_json.get("created_at")

    @staticmethod
    def get_or_create_event_type(event_type_str):
        """Gets or creates an EventType instance by name."""
        return EventType.objects.get_or_create(event_type=event_type_str)[0]

    @staticmethod
    def save_event(repo, event_type_obj, created_at):
        """Saves a new event to the database."""
        Event.objects.create(
            repo=repo,
            event_type=event_type_obj,
            created_at=created_at
        )

    @staticmethod
    def reached_event_limit(repo, event_type_obj, limit):
        """Checks if the event limit per type/repo is reached."""
        return Event.objects.filter(
            repo=repo, event_type=event_type_obj
        ).count() >= limit
