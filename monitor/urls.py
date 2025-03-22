from django.urls import path
from .views import StatsAPIView

urlpatterns = [
    path("stats/", StatsAPIView.as_view(), name="stats"),
]
