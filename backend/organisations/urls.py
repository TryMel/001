from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AppartenanceOrganisationVueSet,
    OrganisationPubliqueVue,
    OrganisationVueSet,
)

routeur = DefaultRouter()
routeur.register(
    "membres",
    AppartenanceOrganisationVueSet,
    basename="membre-organisation",
)
routeur.register("", OrganisationVueSet)
urlpatterns = [
    path(
        "publiques/<int:pk>/",
        OrganisationPubliqueVue.as_view(),
        name="organisation-publique",
    ),
    *routeur.urls,
]
