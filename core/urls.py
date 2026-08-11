from django.urls import path
from .views import SyncReportView, StudentListView, StudentDetailView

urlpatterns = [
    path('reports/sync/', SyncReportView.as_view(), name='sync-report'),
    path('reports/students/', StudentListView.as_view(), name='student-list'),
    path('reports/students/<str:username>/', StudentDetailView.as_view(), name='student-detail'),
]
