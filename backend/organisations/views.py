from django.db import transaction
from django.db.models import Q
from rest_framework import exceptions, permissions, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from comptes.roles import utilisateur_a_role
from .models import AppartenanceOrganisation, Organisation
from .serializers import (
    AppartenanceOrganisationSerializer,
    OrganisationPubliqueSerializer,
    OrganisationSerializer,
)


def est_proprietaire(organisation, utilisateur):
    return organisation.membres.filter(
        utilisateur=utilisateur,
        role=AppartenanceOrganisation.Role.PROPRIETAIRE,
    ).exists()


class OrganisationPubliqueVue(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(tags=["Organisations"], responses=OrganisationPubliqueSerializer)
    def get(self, request, pk):
        try:
            organisation = Organisation.objects.select_related(
                "reference_entreprise",
            ).get(
                pk=pk,
                est_verifiee=True,
            )
        except Organisation.DoesNotExist as erreur:
            raise NotFound("Cette organisation publique n’existe pas.") from erreur
        return Response(
            OrganisationPubliqueSerializer(
                organisation,
                context={"request": request},
            ).data
        )


class OrganisationVueSet(viewsets.ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    search_fields = ("nom", "ville", "pays")

    def get_queryset(self):
        return Organisation.objects.select_related("reference_entreprise").filter(
            membres__utilisateur=self.request.user,
        ).distinct().order_by("pk")

    def perform_create(self, serializer):
        if not utilisateur_a_role(self.request.user, "organisation"):
            raise exceptions.PermissionDenied(
                "Attribuez le rôle organisation avant de créer une organisation."
            )
        with transaction.atomic():
            organisation = serializer.save()
            AppartenanceOrganisation.objects.create(
                organisation=organisation,
                utilisateur=self.request.user,
                role=AppartenanceOrganisation.Role.PROPRIETAIRE,
            )

    def perform_update(self, serializer):
        if not est_proprietaire(serializer.instance, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul un propriétaire actif peut gérer cette organisation."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if not est_proprietaire(instance, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul un propriétaire actif peut gérer cette organisation."
            )
        if instance.opportunites.exists():
            raise exceptions.ValidationError(
                "Cette organisation ne peut pas être supprimée tant que des offres lui sont rattachées."
            )
        instance.delete()


class AppartenanceOrganisationVueSet(viewsets.ModelViewSet):
    serializer_class = AppartenanceOrganisationSerializer

    def get_queryset(self):
        organisations_gerables = AppartenanceOrganisation.objects.filter(
            utilisateur=self.request.user,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        ).values_list("organisation_id", flat=True)
        return (
            AppartenanceOrganisation.objects.filter(
                Q(utilisateur=self.request.user)
                | Q(organisation_id__in=organisations_gerables)
            )
            .select_related(
                "organisation",
                "organisation__reference_entreprise",
                "utilisateur",
            )
            .order_by("organisation_id", "role", "pk")
            .distinct()
        )

    def perform_create(self, serializer):
        organisation = serializer.validated_data["organisation"]
        if not est_proprietaire(organisation, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul un propriétaire actif peut gérer les membres."
            )
        if (
            serializer.validated_data["role"]
            == AppartenanceOrganisation.Role.PROPRIETAIRE
        ):
            raise exceptions.ValidationError(
                {"role": "Le transfert de propriété nécessite une procédure dédiée."}
            )
        serializer.save()

    def perform_update(self, serializer):
        appartenance = serializer.instance
        if not est_proprietaire(appartenance.organisation, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul un propriétaire actif peut gérer les membres."
            )
        if appartenance.role == AppartenanceOrganisation.Role.PROPRIETAIRE:
            raise exceptions.ValidationError(
                {"role": "La propriété ne peut pas être modifiée ici."}
            )
        if (
            serializer.validated_data.get("role")
            == AppartenanceOrganisation.Role.PROPRIETAIRE
        ):
            raise exceptions.ValidationError(
                {"role": "Le transfert de propriété nécessite une procédure dédiée."}
            )
        serializer.save()

    def perform_destroy(self, instance):
        if not est_proprietaire(instance.organisation, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul un propriétaire actif peut gérer les membres."
            )
        if instance.role == AppartenanceOrganisation.Role.PROPRIETAIRE:
            raise exceptions.ValidationError(
                "La dernière propriété ne peut pas être supprimée."
            )
        instance.delete()
