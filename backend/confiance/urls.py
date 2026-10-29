from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    EvaluationVueSet,
    EvaluationsPubliquesVue,
    SignalementVueSet,
    VerificationVueSet,
)

routeur = DefaultRouter()
routeur.register("evaluations", EvaluationVueSet, basename="evaluation")
routeur.register("verifications", VerificationVueSet, basename="verification")
routeur.register("signalements", SignalementVueSet, basename="signalement")

urlpatterns = [
    path(
        "professionnels/<int:profil_id>/evaluations/",
        EvaluationsPubliquesVue.as_view(),
        name="evaluations-publiques",
    ),
] + routeur.urls
