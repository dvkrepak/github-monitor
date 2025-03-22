from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from monitor.models import Repository
from monitor.services.github.analysis import Analyzer


class StatsAPIView(APIView):
    """
    GET /api/stats/?days=7&limit=500

    Returns aggregated statistics per (repository, event_type).

    Response fields:
    - repository: full name (e.g. "tiangolo/fastapi")
    - repository_slug: unique slug (e.g. "tiangolofastapi")
    - event_type: GitHub event type
    - average_interval_seconds: avg time (in seconds) between consecutive events
    - human_readable_interval: formatted average interval (e.g. "3 hours, 20 minutes")
    - event_count: number of events used

    Query params:
    - days (optional): rolling window in days (default: 7)
    - limit (optional): max events per (repo, type) to consider (default: 500)
    """

    @staticmethod
    def get(request):
        try:
            # Parse optional query params
            days = int(request.GET.get("days", 7))
            limit = int(request.GET.get("limit", 500))
        except ValueError:
            return Response(
                {"error": "Parameters 'days' and 'limit' must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        analyzer = Analyzer(days=days, limit=limit)
        stats = analyzer.get_stats()
        return Response(stats, status=status.HTTP_200_OK)


class RepoStatsAPIView(APIView):
    """
    GET /api/stats/<slug>/?days=7&limit=500

    Returns the same stats as StatsAPIView, but scoped to a single repository.

    Path params:
    - slug: unique slug of the repository (auto-generated from name)

    Query params:
    - days (optional): rolling window in days (default: 7)
    - limit (optional): max events per event type to consider (default: 500)
    """

    @staticmethod
    def get(request, slug):
        try:
            days = int(request.GET.get("days", 7))
            limit = int(request.GET.get("limit", 500))
        except ValueError:
            return Response(
                {"error": "Parameters 'days' and 'limit' must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        repo = get_object_or_404(Repository, slug=slug)
        analyzer = Analyzer(days=days, limit=limit)
        stats = analyzer.get_stats(repo=repo)
        return Response(stats, status=status.HTTP_200_OK)
