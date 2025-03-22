import numpy as np
from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings

from monitor.models import Repository, Event, EventType


class Analyzer:
    """
    Analyzer class calculates average time between events per repository and event type.

    The analysis is based on a rolling window defined by number of days or max number of events.
    Values are read from settings (EVENT_FETCH_DAYS and EVENT_FETCH_LIMIT) or passed explicitly.
    """

    def __init__(self, days=None, limit=None):
        # Use values from settings if not overridden
        self.days = days or int(getattr(settings, "EVENT_FETCH_DAYS", 7))
        self.limit = limit or int(getattr(settings, "EVENT_FETCH_LIMIT", 500))
        self.cutoff = now() - timedelta(days=self.days)

    def get_stats(self, repo: Repository = None):
        """
        Returns a list of stats: average interval (in seconds and human-readable) and event count,
        grouped by repository and event type.
        """
        results = []

        repos = [repo] if repo else Repository.objects.filter(active=True)

        for repo in repos:
            event_types = EventType.objects.filter(
                event__repo=repo,
                event__created_at__gte=self.cutoff
            ).distinct()

            for event_type in event_types:
                # Get up to <limit> events for (repo, event_type) in the rolling window
                events = (
                    Event.objects
                    .filter(repo=repo, event_type=event_type, created_at__gte=self.cutoff)
                    .order_by("-created_at")[:self.limit]
                )

                # Maintain chronological order for interval calculation
                events = Event.objects.filter(id__in=events.values_list("id", flat=True)).order_by("created_at")
                timestamps = list(events.values_list("created_at", flat=True))

                avg_interval = self._calculate_average_interval(timestamps)

                results.append({
                    "repository": repo.name,
                    "repository_slug": repo.slug,
                    "event_type": event_type.event_type,
                    "average_interval_seconds": avg_interval,
                    "human_readable_interval": self._format_duration(avg_interval),
                    "event_count": len(timestamps),
                })

        return results

    @staticmethod
    def _calculate_average_interval(timestamps):
        """
        Returns the average time (in seconds) between consecutive datetimes.
        """
        if len(timestamps) < 2:
            return None

        times = np.array([dt.timestamp() for dt in timestamps])
        diffs = np.diff(times)
        return float(np.mean(diffs))

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Converts a duration in seconds into a concise human-readable string.
        Example: "1 hour, 5 minutes", "13 seconds", etc.
        """
        if seconds is None:
            return "N/A"

        seconds = int(seconds)

        intervals = (
            ('year', 60 * 60 * 24 * 365),
            ('month', 60 * 60 * 24 * 30),
            ('day', 60 * 60 * 24),
            ('hour', 60 * 60),
            ('minute', 60),
            ('second', 1),
        )

        result = []

        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                result.append(f"{value} {name}{'s' if value != 1 else ''}")

        return ', '.join(result) if result else "0 seconds"
