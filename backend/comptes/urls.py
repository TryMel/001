from django.urls import path
from .views import (
    ConnexionVue,
    ConfirmationVerificationEmailVue,
    DemandeReinitialisationMotDePasseVue,
    EnvoiVerificationEmailVue,
    DeconnexionVue,
    InscriptionVue,
    MonCompteVue,
    RafraichissementJetonVue,
    ReinitialisationMotDePasseVue,
    RoleActifVue,
    TerminerOnboardingVue,
)

urlpatterns = [
    path("inscription/", InscriptionVue.as_view()),
    path("connexion/", ConnexionVue.as_view()),
    path("rafraichir/", RafraichissementJetonVue.as_view()),
    path("deconnexion/", DeconnexionVue.as_view()),
    path("mot-de-passe/oublie/", DemandeReinitialisationMotDePasseVue.as_view()),
    path("mot-de-passe/reinitialiser/", ReinitialisationMotDePasseVue.as_view()),
    path("verification-email/envoyer/", EnvoiVerificationEmailVue.as_view()),
    path("verification-email/confirmer/", ConfirmationVerificationEmailVue.as_view()),
    path("moi/", MonCompteVue.as_view()),
    path("moi/onboarding/", TerminerOnboardingVue.as_view()),
    path("moi/role-actif/", RoleActifVue.as_view()),
]
