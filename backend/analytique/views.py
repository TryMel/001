from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from comptes.roles import ROLES_FONCTIONNELS
from .models import EvenementInteraction
from .serializers import EvenementInteractionSerializer


class EnregistrerInteractionVue(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Pilotage"],
        request=EvenementInteractionSerializer,
        responses={204: None},
        description="Enregistre une interaction agrégée, sans donnée personnelle ni contenu saisi.",
    )
    def post(self, request):
        formulaire = EvenementInteractionSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)

        role_actif = request.user.role_actif
        if (
            role_actif not in ROLES_FONCTIONNELS
            or role_actif not in request.user.roles_professionnels
        ):
            return Response(
                {"detail": "Terminez le choix de votre espace avant le suivi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        EvenementInteraction.objects.create(
            fonctionnalite=formulaire.validated_data["fonctionnalite"],
            role_actif=role_actif,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
