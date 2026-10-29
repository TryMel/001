from rest_framework.routers import DefaultRouter

from .views import (
    CollaborationVueSet,
    DemandeServiceVueSet,
    JalonVueSet,
    LivrableVueSet,
    OffreServiceVueSet,
    PropositionVueSet,
)

routeur = DefaultRouter()
routeur.register("services", OffreServiceVueSet, basename="offre-service")
routeur.register("demandes", DemandeServiceVueSet, basename="demande-service")
routeur.register("propositions", PropositionVueSet, basename="proposition")
routeur.register("collaborations", CollaborationVueSet, basename="collaboration")
routeur.register("jalons", JalonVueSet, basename="jalon")
routeur.register("livrables", LivrableVueSet, basename="livrable")

urlpatterns = routeur.urls
