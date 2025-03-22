import requests
from django.conf import settings


class GitHubAPIClient:
    """
    Stateless GitHub API client
    """

    @staticmethod
    def get_headers():
        headers = {"Accept": "application/vnd.github+json"}
        token = getattr(settings, 'GITHUB_TOKEN', None)

        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def fetch_repo_events(cls, repo_name: str, page: int = 1):
        """
        Fetches one page of events for a given repository.
        """
        url = f"https://api.github.com/repos/{repo_name}/events?per_page=100&page={page}"
        return requests.get(url, headers=cls.get_headers())
