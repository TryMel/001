from django.db.models import Avg, F, Max, Min, Q
from rest_framework import exceptions, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from profils.models import ProfilProfessionnel
from profils.roles import utilisateur_peut_gerer_profil

from collaborations.models import Collaboration
from .models import Evaluation, Signalement, Verification
from .serializers import (
    EvaluationPubliqueSerializer,
    EvaluationSerializer,
    SignalementSerializer,
    VerificationSerializer,
)


class EvaluationVueSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        utilisateur = self.request.user
        return Evaluation.objects.filter(
            Q(evalue=utilisateur) | Q(auteur=utilisateur)
        ).select_related("evalue", "auteur", "collaboration")


class EvaluationsPubliquesVue(APIView):
    permission_classes = (permissions.AllowAny,)
    SEUIL_AVIS_NOTE = 5

    @extend_schema(
        tags=["Confiance"],
        responses=inline_serializer(
            name="ResultatEvaluationsPubliques",
            fields={
                "nombre": serializers.IntegerField(),
                "moyenne": serializers.FloatField(allow_null=True),
                "message": serializers.CharField(allow_null=True),
                "seuil": serializers.IntegerField(),
                "periode": inline_serializer(
                    name="PeriodeEvaluationsPubliques",
                    fields={
                        "debut": serializers.DateField(allow_null=True),
                        "fin": serializers.DateField(allow_null=True),
                    },
                ),
                "resultats": EvaluationPubliqueSerializer(many=True),
            },
        ),
    )
    def get(self, request, profil_id):
        try:
            profil = ProfilProfessionnel.objects.get(
                pk=profil_id,
                visible_publiquement=True,
                utilisateur__is_active=True,
                utilisateur__onboarding_termine=True,
            )
        except ProfilProfessionnel.DoesNotExist as erreur:
            raise exceptions.NotFound("Ce profil public n’existe pas.") from erreur
        if not utilisateur_peut_gerer_profil(profil.utilisateur):
            raise exceptions.NotFound("Ce profil public n’existe pas.")
        evaluations = Evaluation.objects.filter(
            evalue=profil.utilisateur,
            statut=Evaluation.Statut.PUBLIEE,
            collaboration__statut=Collaboration.Statut.TERMINEE,
        ).filter(
            Q(
                collaboration__client_id=F("auteur_id"),
                collaboration__prestataire_id=F("evalue_id"),
            )
            | Q(
                collaboration__client_id=F("evalue_id"),
                collaboration__prestataire_id=F("auteur_id"),
            )
        ).select_related("auteur", "collaboration")
        aggregation = evaluations.aggregate(
            moyenne=Avg("note"),
            premiere=Min("cree_le"),
            derniere=Max("cree_le"),
        )
        nombre = evaluations.count()
        score_disponible = nombre >= self.SEUIL_AVIS_NOTE
        return Response(
            {
                "nombre": nombre,
                "moyenne": (
                    round(aggregation["moyenne"], 1)
                    if score_disponible and aggregation["moyenne"] is not None
                    else None
                ),
                "message": None if score_disponible else "Pas encore assez d’avis",
                "seuil": self.SEUIL_AVIS_NOTE,
                "periode": {
                    "debut": (
                        aggregation["premiere"].date().isoformat()
                        if aggregation["premiere"]
                        else None
                    ),
                    "fin": (
                        aggregation["derniere"].date().isoformat()
                        if aggregation["derniere"]
                        else None
                    ),
                },
                "resultats": EvaluationPubliqueSerializer(
                    evaluations,
                    many=True,
                ).data,
            }
        )


class VerificationVueSet(viewsets.ModelViewSet):
    serializer_class = VerificationSerializer
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return Verification.objects.filter(
            utilisateur=self.request.user
        ).select_related("utilisateur")


class SignalementVueSet(viewsets.ModelViewSet):
    serializer_class = SignalementSerializer
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return Signalement.objects.filter(
            auteur=self.request.user
        ).select_related("cible", "evaluation")
