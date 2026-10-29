from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from confiance.models import Signalement, Verification
from opportunites.models import Opportunite
from organisations.models import Organisation
from profils.models import ProfilProfessionnel


class VueTableauBordAdministration(APIView):
    permission_classes = (IsAdminUser,)
    api_version = "v2"

    def get(self, request):
        utilisateur = get_user_model()
        return Response(
            {
                "version": self.api_version,
                "comptes": utilisateur.objects.count(),
                "profils_visibles": ProfilProfessionnel.objects.filter(
                    visible_publiquement=True,
                    utilisateur__is_active=True,
                    utilisateur__onboarding_termine=True,
                ).count(),
                "opportunites_publiees": Opportunite.objects.filter(
                    statut=Opportunite.Statut.PUBLIEE
                ).count(),
                "organisations_a_verifier": Organisation.objects.filter(
                    est_verifiee=False
                ).count(),
                "verifications_en_attente": Verification.objects.filter(
                    statut=Verification.Statut.EN_ATTENTE
                ).count(),
                "signalements_ouverts": Signalement.objects.filter(
                    statut=Signalement.Statut.OUVERT
                ).count(),
            }
        )
