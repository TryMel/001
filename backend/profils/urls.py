from django.urls import path
from .views import (
    DisponibiliteActuelleVue,
    DisponibilitePubliqueVue,
    ProfilActuelVue,
    ProfilPublicVue,
)

urlpatterns = [
    path("moi/", ProfilActuelVue.as_view(), name="profil-actuel"),
    path(
        "moi/disponibilites/",
        DisponibiliteActuelleVue.as_view(),
        name="disponibilite-actuelle",
    ),
    path("<int:pk>/", ProfilPublicVue.as_view(), name="profil-public"),
    path(
        "<int:pk>/disponibilites/",
        DisponibilitePubliqueVue.as_view(),
        name="disponibilite-publique",
    ),
]
