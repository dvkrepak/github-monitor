from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .analysis import Analyzer


class StatsAPIView(APIView):
    """
    GET /api/stats/?days=7&limit=500

    Returns a list of statistics per (repository, event_type) based on a rolling window.
    Each result includes:
    - average interval between events (in seconds)
    - human-readable duration
    - number of events considered

    Optional query parameters:
    - days: Number of days to include (default: 7)
    - limit: Max number of events to consider per group (default: 500)
    """

    def get(self, request):
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
