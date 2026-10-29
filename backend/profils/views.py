from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .roles import utilisateur_peut_gerer_profil
from .models import DisponibiliteProfil, ProfilProfessionnel
from .serializers import (
    DisponibiliteProfilSerializer,
    ProfilPublicSerializer,
    ProfilSerializer,
)


@extend_schema_view(
    get=extend_schema(tags=["Profils"], responses=ProfilSerializer),
    patch=extend_schema(tags=["Profils"], request=ProfilSerializer, responses=ProfilSerializer),
    put=extend_schema(tags=["Profils"], request=ProfilSerializer, responses=ProfilSerializer),
)
class ProfilActuelVue(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def profil_actuel(self, utilisateur):
        if not utilisateur_peut_gerer_profil(utilisateur):
            raise PermissionDenied(
                "Un espace professionnel, candidat ou étudiant doit être attribué "
                "pour gérer ce profil."
            )
        from .models import ProfilProfessionnel

        profil, _ = ProfilProfessionnel.objects.get_or_create(
            utilisateur=utilisateur
        )
        return profil

    def get(self, request):
        profil = self.profil_actuel(request.user)
        return Response(
            ProfilSerializer(profil, context={"request": request}).data
        )

    def patch(self, request):
        profil = self.profil_actuel(request.user)
        serializer = ProfilSerializer(
            profil, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        profil = self.profil_actuel(request.user)
        serializer = ProfilSerializer(
            profil, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProfilPublicVue(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(tags=["Profils"], responses=ProfilPublicSerializer)
    def get(self, request, pk):
        from django.db.models import Prefetch

        from .roles import utilisateur_peut_gerer_profil
        from .models import NiveauCompetence, ProfilProfessionnel

        try:
            profil = (
                ProfilProfessionnel.objects.filter(
                    pk=pk,
                    visible_publiquement=True,
                    utilisateur__is_active=True,
                    utilisateur__onboarding_termine=True,
                )
                .select_related("utilisateur", "metier")
                .prefetch_related(
                    Prefetch(
                        "niveaucompetence_set",
                        queryset=NiveauCompetence.objects.select_related("competence"),
                    ),
                    "experiences",
                    "formations",
                    "realisations",
                    "realisations__images",
                    "qualifications",
                )
                .get()
            )
        except ProfilProfessionnel.DoesNotExist as erreur:
            raise NotFound("Ce profil public n’existe pas.") from erreur

        if not utilisateur_peut_gerer_profil(profil.utilisateur):
            raise NotFound("Ce profil public n’existe pas.")

        return Response(
            ProfilPublicSerializer(profil, context={"request": request}).data
        )


@extend_schema_view(
    get=extend_schema(tags=["Profils"], responses=DisponibiliteProfilSerializer),
    put=extend_schema(tags=["Profils"], request=DisponibiliteProfilSerializer, responses=DisponibiliteProfilSerializer),
)
class DisponibiliteActuelleVue(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_disponibilite(self, utilisateur):
        profil = ProfilActuelVue().profil_actuel(utilisateur)
        disponibilite, _ = DisponibiliteProfil.objects.get_or_create(profil=profil)
        return (
            DisponibiliteProfil.objects.filter(pk=disponibilite.pk)
            .prefetch_related("creneaux", "exceptions")
            .get()
        )

    def get(self, request):
        disponibilite = self.get_disponibilite(request.user)
        return Response(DisponibiliteProfilSerializer(disponibilite).data)

    def put(self, request):
        disponibilite = self.get_disponibilite(request.user)
        serializer = DisponibiliteProfilSerializer(
            disponibilite,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DisponibilitePubliqueVue(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(tags=["Profils"], responses=DisponibiliteProfilSerializer)
    def get(self, request, pk):
        try:
            profil = ProfilProfessionnel.objects.get(
                pk=pk,
                visible_publiquement=True,
                utilisateur__is_active=True,
                utilisateur__onboarding_termine=True,
            )
        except ProfilProfessionnel.DoesNotExist as erreur:
            raise NotFound("Cette disponibilité publique n’existe pas.") from erreur
        if not utilisateur_peut_gerer_profil(profil.utilisateur):
            raise NotFound("Cette disponibilité publique n’existe pas.")
        disponibilite = (
            DisponibiliteProfil.objects.filter(profil=profil)
            .prefetch_related("creneaux", "exceptions")
            .first()
        )
        if disponibilite is None:
            return Response(
                {"fuseau": "Africa/Abidjan", "creneaux": [], "exceptions": []}
            )
        return Response(DisponibiliteProfilSerializer(disponibilite).data)
