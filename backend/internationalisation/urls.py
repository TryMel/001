from rest_framework.routers import DefaultRouter

from .views import (
    EntrepriseReferenceVueSet,
    EtablissementReferenceVueSet,
    MarcheVueSet,
    ProgrammeFormationReferenceVueSet,
    RegleMetierLocaleVueSet,
    VilleVueSet,
)

routeur = DefaultRouter()
routeur.register("marches", MarcheVueSet)
routeur.register("regles", RegleMetierLocaleVueSet)
routeur.register("villes", VilleVueSet, basename="ville")
routeur.register(
    "entreprises",
    EntrepriseReferenceVueSet,
    basename="entreprise-reference",
)
routeur.register(
    "etablissements",
    EtablissementReferenceVueSet,
    basename="etablissement-reference",
)
routeur.register(
    "programmes-formation",
    ProgrammeFormationReferenceVueSet,
    basename="programme-formation-reference",
)

urlpatterns = routeur.urls
