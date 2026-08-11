from django.urls import path
from .views import CompetenceListView, QuestionsByLevelView

urlpatterns = [
    path('competences/', CompetenceListView.as_view(), name='competence-list'),
    path('questions/<int:level_id>/', QuestionsByLevelView.as_view(), name='questions-by-level'),
]
