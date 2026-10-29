from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from profils.models import ProfilProfessionnel
from profils.roles import utilisateur_peut_gerer_profil
from .models import Experience, Formation, Qualification, Realisation
from .serializers import ExperienceSerializer, FormationSerializer, QualificationSerializer, RealisationSerializer


class PossessionProfilVueSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def _verifier_role(self):
        if not utilisateur_peut_gerer_profil(self.request.user):
            raise PermissionDenied(
                "Un espace professionnel, candidat ou étudiant doit être attribué "
                "pour gérer ce portfolio."
            )

    def get_queryset(self):
        self._verifier_role()
        return self.queryset.filter(profil__utilisateur=self.request.user)

    def perform_create(self, serializer):
        self._verifier_role()
        profil, _ = ProfilProfessionnel.objects.get_or_create(
            utilisateur=self.request.user
        )
        serializer.save(profil=profil)


class FormationVueSet(PossessionProfilVueSet):
    queryset = Formation.objects.select_related(
        "etablissement_reference",
        "programme_reference",
    )
    serializer_class = FormationSerializer


class ExperienceVueSet(PossessionProfilVueSet):
    queryset = Experience.objects.select_related("entreprise_reference")
    serializer_class = ExperienceSerializer


class RealisationVueSet(PossessionProfilVueSet):
    queryset = Realisation.objects.prefetch_related("images")
    serializer_class = RealisationSerializer


class QualificationVueSet(PossessionProfilVueSet):
    queryset = Qualification.objects.all()
    serializer_class = QualificationSerializer
