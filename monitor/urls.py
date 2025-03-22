from django.urls import path
from .views import StatsAPIView, RepoStatsAPIView

urlpatterns = [
    path("stats/", StatsAPIView.as_view(), name="stats"),
    path("stats/<slug:slug>/", RepoStatsAPIView.as_view()),
]
