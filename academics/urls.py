from django.urls import path
from .views import CompetenceListView, IconoDeNivelView, QuestionsByLevelView

urlpatterns = [
    path('competences/', CompetenceListView.as_view(), name='competence-list'),
    path('questions/<int:level_id>/', QuestionsByLevelView.as_view(), name='questions-by-level'),

    # La version va EN la ruta, no como `?v=`, porque algunas caches —y Coil
    # entre ellas, segun como se configure— ignoran la cadena de consulta al
    # construir la clave. Metida en el camino, una version nueva es una URL
    # distinta y no hay forma de confundirlas.
    path(
        'levels/<int:level_id>/icono/<int:version>/',
        IconoDeNivelView.as_view(),
        name='icono-de-nivel',
    ),
]
