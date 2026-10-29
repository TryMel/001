from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from rest_framework import exceptions, mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.models import Notification
from organisations.models import AppartenanceOrganisation
from portfolios.models import Experience, Formation

from .models import Candidature, HistoriqueCandidature, Opportunite
from .permissions import (
    ROLES_RECRUTEMENT_ORGANISATION,
    peut_gerer_opportunite,
)
from .serializers import (
    CandidatureSerializer,
    FiltresOpportuniteSerializer,
    OpportuniteSerializer,
)


class ConflitCandidature(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "La candidature a été modifiée. Rechargez-la avant de réessayer."
    default_code = "conflit_candidature"


class TransitionCandidatureSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=Candidature.Statut.choices)
    expected_version = serializers.IntegerField(min_value=1)
    motif = serializers.CharField(max_length=500, required=False, allow_blank=True)


class OpportuniteVueSet(viewsets.ModelViewSet):
    queryset = Opportunite.objects.select_related(
        "createur",
        "organisation",
        "metier",
    ).prefetch_related("competences", "images")
    serializer_class = OpportuniteSerializer
    search_fields = ("titre", "description", "ville", "metier__nom", "competences__nom")
    ordering_fields = ("cree_le", "titre", "ville", "type")
    ordering = ("-cree_le",)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        publique = Q(statut=Opportunite.Statut.PUBLIEE)
        if not self.request.user.is_authenticated:
            return queryset.filter(publique)
        organisations_gerables = AppartenanceOrganisation.objects.filter(
            utilisateur=self.request.user,
            role__in=ROLES_RECRUTEMENT_ORGANISATION,
        ).values_list("organisation_id", flat=True)
        return queryset.filter(
            publique
            | Q(createur=self.request.user, organisation__isnull=True)
            | Q(organisation_id__in=organisations_gerables)
        ).distinct()

    def filter_queryset(self, queryset):
        filtres = FiltresOpportuniteSerializer(data=self.request.query_params)
        filtres.is_valid(raise_exception=True)
        donnees = filtres.validated_data
        queryset = super().filter_queryset(queryset)
        for champ in ("statut", "type", "contrat", "metier", "pays"):
            if champ in donnees:
                valeur = donnees[champ]
                queryset = queryset.filter(**{champ: valeur.upper() if champ == "pays" else valeur})
        if "devise" in donnees:
            queryset = queryset.filter(devise__iexact=donnees["devise"])
        if "ville" in donnees:
            queryset = queryset.filter(ville__icontains=donnees["ville"].strip())
        if "competence" in donnees:
            queryset = queryset.filter(competences__pk=donnees["competence"])
        if "budget_min" in donnees:
            queryset = queryset.filter(
                Q(budget_maximum__gte=donnees["budget_min"])
                | Q(budget_maximum__isnull=True)
            )
        if "budget_max" in donnees:
            queryset = queryset.filter(
                Q(budget_minimum__lte=donnees["budget_max"])
                | Q(budget_minimum__isnull=True)
            )
        return queryset.distinct()

    def perform_update(self, serializer):
        if not peut_gerer_opportunite(serializer.instance, self.request.user):
            raise exceptions.PermissionDenied("Vous ne gérez pas cette opportunité.")
        serializer.save()

    def perform_destroy(self, instance):
        if not peut_gerer_opportunite(instance, self.request.user):
            raise exceptions.PermissionDenied("Vous ne gérez pas cette opportunité.")
        instance.delete()

    @action(detail=True, methods=("post",))
    def publier(self, request, pk=None):
        opportunite = self.get_object()
        if not peut_gerer_opportunite(opportunite, request.user):
            raise exceptions.PermissionDenied(
                "Vous ne gérez pas cette opportunité."
            )
        if opportunite.statut != Opportunite.Statut.BROUILLON:
            raise exceptions.ValidationError(
                {"statut": "Seule une offre en brouillon peut être publiée."}
            )
        if opportunite.organisation_id and not opportunite.organisation.est_verifiee:
            raise exceptions.ValidationError(
                {"organisation": "L’organisation doit être vérifiée avant publication."}
            )
        if not opportunite.images.exists():
            raise exceptions.ValidationError(
                {"images": "Ajoutez au moins une image avant de publier cette opportunite."}
            )
        opportunite.statut = Opportunite.Statut.PUBLIEE
        opportunite.save(update_fields=("statut",))
        return Response(self.get_serializer(opportunite).data)


class CandidatureVueSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CandidatureSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Candidature.objects.select_related(
            "opportunite",
            "candidat",
        ).prefetch_related("historique")
        if self.action in ("recues", "transition"):
            if self.action == "recues":
                queryset = queryset.prefetch_related(
                    "candidat__profil__niveaucompetence_set__competence",
                    Prefetch(
                        "candidat__profil__experiences",
                        queryset=Experience.objects.select_related(
                            "entreprise_reference"
                        ),
                    ),
                    Prefetch(
                        "candidat__profil__formations",
                        queryset=Formation.objects.select_related(
                            "etablissement_reference",
                            "programme_reference",
                        ),
                    ),
                    "candidat__profil__realisations__images",
                    "candidat__profil__qualifications",
                )
            organisations_gerables = AppartenanceOrganisation.objects.filter(
                utilisateur=self.request.user,
                role__in=ROLES_RECRUTEMENT_ORGANISATION,
            ).values_list("organisation_id", flat=True)
            queryset = queryset.filter(
                Q(
                    opportunite__createur=self.request.user,
                    opportunite__organisation__isnull=True,
                )
                | Q(opportunite__organisation_id__in=organisations_gerables)
            ).distinct()
            if self.action == "transition":
                queryset = queryset.select_for_update()
            return queryset
        return queryset.filter(candidat=self.request.user)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                candidature = serializer.save(candidat=self.request.user)
                HistoriqueCandidature.objects.create(
                    candidature=candidature,
                    acteur=self.request.user,
                    nouveau_statut=candidature.statut,
                )
                Notification.objects.create(
                    utilisateur=candidature.opportunite.createur,
                    titre="Nouvelle candidature",
                    message=f"Une candidature a été reçue pour « {candidature.opportunite.titre} ».",
                    lien=f"/api/opportunites/candidatures/{candidature.pk}/",
                )
        except IntegrityError as erreur:
            raise serializers.ValidationError(
                {"opportunite": "Vous avez déjà candidaté à cette opportunité."}
            ) from erreur

    @action(detail=False, methods=("get",))
    def recues(self, request):
        candidatures = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(candidatures)
        if page is not None:
            donnees = self.get_serializer(page, many=True).data
            return self.get_paginated_response(donnees)
        return Response(self.get_serializer(candidatures, many=True).data)

    @action(detail=True, methods=("post",))
    def transition(self, request, pk=None):
        formulaire = TransitionCandidatureSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        cible = formulaire.validated_data["statut"]

        transitions = {
            Candidature.Statut.ENVOYEE: {
                Candidature.Statut.EN_COURS,
                Candidature.Statut.RETENUE,
                Candidature.Statut.ENTRETIEN,
                Candidature.Statut.OFFRE,
                Candidature.Statut.REFUSEE,
            },
            Candidature.Statut.EN_COURS: {
                Candidature.Statut.RETENUE,
                Candidature.Statut.ENTRETIEN,
                Candidature.Statut.OFFRE,
                Candidature.Statut.REFUSEE,
            },
            Candidature.Statut.RETENUE: {
                Candidature.Statut.ENTRETIEN,
                Candidature.Statut.OFFRE,
                Candidature.Statut.REFUSEE,
            },
            Candidature.Statut.ENTRETIEN: {
                Candidature.Statut.OFFRE,
                Candidature.Statut.REFUSEE,
            },
            Candidature.Statut.OFFRE: {
                Candidature.Statut.ACCEPTEE,
                Candidature.Statut.REFUSEE,
            },
        }

        with transaction.atomic():
            candidature = self.get_object()
            if candidature.version != formulaire.validated_data["expected_version"]:
                raise ConflitCandidature()
            if cible not in transitions.get(candidature.statut, set()):
                raise exceptions.ValidationError(
                    {"statut": "Cette transition de candidature n'est pas autorisée."}
                )

            statut_precedent = candidature.statut
            candidature.statut = cible
            candidature.version += 1
            candidature.save(update_fields=("statut", "version"))
            HistoriqueCandidature.objects.create(
                candidature=candidature,
                acteur=request.user,
                statut_precedent=statut_precedent,
                nouveau_statut=cible,
                motif=formulaire.validated_data.get("motif", ""),
            )
            Notification.objects.create(
                utilisateur=candidature.candidat,
                titre="Mise à jour de candidature",
                message=(
                    f"Le statut de votre candidature pour « "
                    f"{candidature.opportunite.titre} » a été mis à jour."
                ),
                lien=f"/api/opportunites/candidatures/{candidature.pk}/",
            )

        return Response(self.get_serializer(candidature).data)

    @action(detail=True, methods=("post",))
    def retirer(self, request, pk=None):
        with transaction.atomic():
            candidature = self.get_object()
            if candidature.statut in (
                Candidature.Statut.ACCEPTEE,
                Candidature.Statut.REFUSEE,
                Candidature.Statut.RETIREE,
            ):
                raise exceptions.ValidationError(
                    {"statut": "Cette candidature ne peut plus être retirée."}
                )
            statut_precedent = candidature.statut
            candidature.statut = Candidature.Statut.RETIREE
            candidature.version += 1
            candidature.save(update_fields=("statut", "version"))
            HistoriqueCandidature.objects.create(
                candidature=candidature,
                acteur=request.user,
                statut_precedent=statut_precedent,
                nouveau_statut=candidature.statut,
            )
        return Response(self.get_serializer(candidature).data)
