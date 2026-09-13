from django.urls import path
from .views import SyncReportView, StudentListView, StudentDetailView, RankingView, DashboardDataAPIView

urlpatterns = [
    path('reports/sync/', SyncReportView.as_view(), name='sync-report'),
    path('reports/students/', StudentListView.as_view(), name='student-list'),
    path('reports/students/<str:username>/', StudentDetailView.as_view(), name='student-detail'),
    path('ranking/', RankingView.as_view(), name='ranking'),
    path('dashboard-data/', DashboardDataAPIView.as_view(), name='dashboard-data'),
]
