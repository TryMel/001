from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import exceptions, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from organisations.models import AppartenanceOrganisation

from .models import (
    Collaboration,
    DemandeService,
    Jalon,
    Livrable,
    OffreService,
    Proposition,
)
from .permissions import (
    peut_gerer_demande,
    peut_gerer_collaboration,
    peut_proposer,
    represente_client_collaboration,
)
from .serializers import (
    CollaborationSerializer,
    DemandeServiceSerializer,
    JalonSerializer,
    LivrableSerializer,
    OffreServiceSerializer,
    PropositionCreationSerializer,
    PropositionSerializer,
)


class ConflitEtat(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflit_etat"


class OffreServiceVueSet(viewsets.ModelViewSet):
    serializer_class = OffreServiceSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return (permissions.AllowAny(),)
        return (permissions.IsAuthenticated(),)

    def get_queryset(self):
        queryset = OffreService.objects.select_related(
            "profil__utilisateur",
            "profil__metier",
        ).prefetch_related("competences", "images")
        publique = Q(
            statut=OffreService.Statut.PUBLIEE,
            profil__visible_publiquement=True,
            profil__utilisateur__is_active=True,
            profil__utilisateur__onboarding_termine=True,
        )
        utilisateur = self.request.user
        if utilisateur.is_authenticated:
            personnelle = Q(profil__utilisateur=utilisateur)
            return queryset.filter(publique | personnelle).distinct()
        return queryset.filter(publique)

    def perform_update(self, serializer):
        offre = serializer.instance
        if offre.profil.utilisateur_id != self.request.user.pk:
            raise exceptions.PermissionDenied(
                "Seul le propriétaire peut modifier ce service."
            )
        if offre.statut == OffreService.Statut.FERMEE:
            raise ConflitEtat("Un service fermé ne peut pas être modifié.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.profil.utilisateur_id != self.request.user.pk:
            raise exceptions.PermissionDenied(
                "Seul le propriétaire peut supprimer ce brouillon."
            )
        if instance.statut != OffreService.Statut.BROUILLON:
            raise ConflitEtat("Seul un brouillon peut être supprimé.")
        instance.delete()

    @action(detail=True, methods=("post",))
    def publier(self, request, pk=None):
        offre = self.get_object()
        if offre.profil.utilisateur_id != request.user.pk:
            raise exceptions.PermissionDenied("Seul le propriétaire peut publier.")
        if offre.statut != OffreService.Statut.BROUILLON:
            raise ConflitEtat("Seul un brouillon peut être publié.")
        if not offre.profil.visible_publiquement:
            raise exceptions.ValidationError(
                "Rendez votre profil professionnel visible avant de publier un service."
            )
        if not offre.photo and not offre.images.exists():
            raise exceptions.ValidationError(
                {"images": "Ajoutez une photo ou une image avant de publier ce service."}
            )
        offre.statut = OffreService.Statut.PUBLIEE
        offre.save(update_fields=("statut", "modifie_le"))
        return Response(self.get_serializer(offre).data)

    @action(detail=True, methods=("post",))
    def fermer(self, request, pk=None):
        offre = self.get_object()
        if offre.profil.utilisateur_id != request.user.pk:
            raise exceptions.PermissionDenied("Seul le propriétaire peut fermer.")
        if offre.statut != OffreService.Statut.PUBLIEE:
            raise ConflitEtat("Seul un service publié peut être fermé.")
        offre.statut = OffreService.Statut.FERMEE
        offre.save(update_fields=("statut", "modifie_le"))
        return Response(self.get_serializer(offre).data)


class DemandeServiceVueSet(viewsets.ModelViewSet):
    serializer_class = DemandeServiceSerializer

    def get_queryset(self):
        queryset = DemandeService.objects.select_related(
            "client",
            "organisation",
        ).prefetch_related("competences", "images")
        utilisateur = self.request.user
        organisations = AppartenanceOrganisation.objects.filter(
            utilisateur=utilisateur,
            role__in=(
                AppartenanceOrganisation.Role.PROPRIETAIRE,
                AppartenanceOrganisation.Role.GESTIONNAIRE,
            ),
        ).values_list("organisation_id", flat=True)
        personnelle = Q(client=utilisateur) | Q(organisation_id__in=organisations)
        publique = (
            Q(
                visibilite=DemandeService.Visibilite.PUBLIQUE,
                statut__in=(
                    DemandeService.Statut.OUVERTE,
                    DemandeService.Statut.EN_DISCUSSION,
                ),
            )
            if peut_proposer(utilisateur)
            else Q(pk__in=[])
        )
        return queryset.filter(personnelle | publique).distinct()

    def perform_update(self, serializer):
        demande = serializer.instance
        if not peut_gerer_demande(demande, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul le client ou un gestionnaire autorisé peut modifier la demande."
            )
        if demande.statut not in (
            DemandeService.Statut.BROUILLON,
            DemandeService.Statut.OUVERTE,
        ):
            raise ConflitEtat("Cette demande ne peut plus être modifiée.")
        serializer.save()

    def perform_destroy(self, instance):
        if not peut_gerer_demande(instance, self.request.user):
            raise exceptions.PermissionDenied(
                "Seul le client ou un gestionnaire autorisé peut supprimer la demande."
            )
        if instance.statut != DemandeService.Statut.BROUILLON:
            raise ConflitEtat("Seul un brouillon peut être supprimé.")
        instance.delete()

    @action(detail=True, methods=("post",))
    def publier(self, request, pk=None):
        demande = self.get_object()
        if not peut_gerer_demande(demande, request.user):
            raise exceptions.PermissionDenied("Vous ne pouvez pas publier cette demande.")
        if demande.statut != DemandeService.Statut.BROUILLON:
            raise ConflitEtat("Seul un brouillon peut être publié.")
        if demande.organisation_id and not demande.organisation.est_verifiee:
            raise exceptions.ValidationError(
                "L’organisation doit être vérifiée avant la publication."
            )
        if not demande.titre.strip() or not demande.description.strip():
            raise exceptions.ValidationError(
                "Le titre et la description sont obligatoires."
            )
        if not demande.photo and not demande.images.exists():
            raise exceptions.ValidationError(
                {"images": "Ajoutez une photo ou une image avant de publier cette demande."}
            )
        demande.statut = DemandeService.Statut.OUVERTE
        demande.publie_le = timezone.now()
        demande.save(update_fields=("statut", "publie_le", "modifie_le"))
        return Response(self.get_serializer(demande).data)

    @action(detail=True, methods=("post",))
    def fermer(self, request, pk=None):
        demande = self.get_object()
        if not peut_gerer_demande(demande, request.user):
            raise exceptions.PermissionDenied("Vous ne pouvez pas fermer cette demande.")
        if demande.statut not in (
            DemandeService.Statut.OUVERTE,
            DemandeService.Statut.EN_DISCUSSION,
        ):
            raise ConflitEtat("Cette demande ne peut plus être fermée.")
        demande.statut = DemandeService.Statut.FERMEE
        demande.save(update_fields=("statut", "modifie_le"))
        demande.propositions.filter(statut=Proposition.Statut.SOUMISE).update(
            statut=Proposition.Statut.REFUSEE,
            modifie_le=timezone.now(),
        )
        return Response(self.get_serializer(demande).data)

    @action(detail=True, methods=("get", "post"), url_path="propositions")
    def propositions(self, request, pk=None):
        demande = self.get_object()
        if request.method == "GET":
            if not peut_gerer_demande(demande, request.user):
                raise exceptions.PermissionDenied(
                    "Seul le client peut consulter les propositions reçues."
                )
            donnees = PropositionSerializer(
                demande.propositions.select_related("prestataire").all(),
                many=True,
                context={"request": request},
            ).data
            return Response(donnees)

        if not peut_proposer(request.user):
            raise exceptions.PermissionDenied(
                "Un profil professionnel actif est requis pour proposer un service."
            )
        est_membre_organisation = (
            demande.organisation_id is not None
            and AppartenanceOrganisation.objects.filter(
                organisation_id=demande.organisation_id,
                utilisateur=request.user,
            ).exists()
        )
        if demande.client_id == request.user.pk or est_membre_organisation:
            raise exceptions.ValidationError(
                "Vous ne pouvez pas répondre à votre propre demande."
            )
        if demande.statut not in (
            DemandeService.Statut.OUVERTE,
            DemandeService.Statut.EN_DISCUSSION,
        ):
            raise ConflitEtat("Cette demande n’accepte plus de proposition.")
        serializer = PropositionCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["devise"].upper() != demande.devise:
            raise exceptions.ValidationError(
                {"devise": "La proposition doit utiliser la devise de la demande."}
            )
        if Proposition.objects.filter(
            demande=demande,
            prestataire=request.user,
            statut__in=(
                Proposition.Statut.SOUMISE,
                Proposition.Statut.ACCEPTEE,
            ),
        ).exists():
            raise ConflitEtat("Vous avez déjà soumis une proposition pour cette demande.")
        proposition = Proposition.objects.create(
            demande=demande,
            prestataire=request.user,
            **serializer.validated_data,
        )
        if demande.statut == DemandeService.Statut.OUVERTE:
            demande.statut = DemandeService.Statut.EN_DISCUSSION
            demande.save(update_fields=("statut", "modifie_le"))
        return Response(
            PropositionSerializer(proposition, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PropositionVueSet(viewsets.ModelViewSet):
    serializer_class = PropositionSerializer
    http_method_names = ("get", "patch", "post", "head", "options")

    def get_queryset(self):
        utilisateur = self.request.user
        organisations = AppartenanceOrganisation.objects.filter(
            utilisateur=utilisateur,
            role__in=(
                AppartenanceOrganisation.Role.PROPRIETAIRE,
                AppartenanceOrganisation.Role.GESTIONNAIRE,
            ),
        ).values_list("organisation_id", flat=True)
        return (
            Proposition.objects.filter(
                Q(prestataire=utilisateur)
                | Q(demande__client=utilisateur)
                | Q(demande__organisation_id__in=organisations)
            )
            .select_related("demande", "demande__organisation", "prestataire")
            .distinct()
        )

    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("POST")

    def perform_update(self, serializer):
        proposition = serializer.instance
        if proposition.statut != Proposition.Statut.SOUMISE:
            raise ConflitEtat("Cette proposition ne peut plus être modifiée.")
        serializer.save()

    @action(detail=True, methods=("post",))
    @transaction.atomic
    def accepter(self, request, pk=None):
        proposition = self.get_queryset().select_for_update().filter(pk=pk).first()
        if proposition is None:
            raise exceptions.NotFound()
        if not peut_gerer_demande(proposition.demande, request.user):
            raise exceptions.PermissionDenied(
                "Seul le client ou le gestionnaire autorisé peut accepter."
            )
        demande = DemandeService.objects.select_for_update().get(
            pk=proposition.demande_id
        )
        if proposition.statut != Proposition.Statut.SOUMISE:
            raise ConflitEtat("Cette proposition n’est plus disponible.")
        if demande.statut not in (
            DemandeService.Statut.OUVERTE,
            DemandeService.Statut.EN_DISCUSSION,
        ):
            raise ConflitEtat("Cette demande n’accepte plus d’acceptation.")
        proposition.statut = Proposition.Statut.ACCEPTEE
        proposition.save(update_fields=("statut", "modifie_le"))
        demande.statut = DemandeService.Statut.ATTRIBUEE
        demande.save(update_fields=("statut", "modifie_le"))
        demande.propositions.exclude(pk=proposition.pk).filter(
            statut=Proposition.Statut.SOUMISE
        ).update(
            statut=Proposition.Statut.REFUSEE,
            modifie_le=timezone.now(),
        )
        collaboration = Collaboration.objects.create(
            demande=demande,
            proposition=proposition,
            client=demande.client,
            prestataire=proposition.prestataire,
            perimetre=proposition.message,
            montant=proposition.montant,
            devise=proposition.devise,
        )
        return Response(
            CollaborationSerializer(
                collaboration,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=("post",))
    def retirer(self, request, pk=None):
        proposition = self.get_object()
        if proposition.prestataire_id != request.user.pk:
            raise exceptions.PermissionDenied("Seul l’auteur peut retirer la proposition.")
        if proposition.statut != Proposition.Statut.SOUMISE:
            raise ConflitEtat("Cette proposition ne peut plus être retirée.")
        proposition.statut = Proposition.Statut.RETIREE
        proposition.save(update_fields=("statut", "modifie_le"))
        return Response(self.get_serializer(proposition).data)


class CollaborationVueSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CollaborationSerializer

    def get_queryset(self):
        organisations = AppartenanceOrganisation.objects.filter(
            utilisateur=self.request.user,
            role__in=(
                AppartenanceOrganisation.Role.PROPRIETAIRE,
                AppartenanceOrganisation.Role.GESTIONNAIRE,
            ),
        ).values_list("organisation_id", flat=True)
        return (
            Collaboration.objects.filter(
                Q(client=self.request.user)
                | Q(prestataire=self.request.user)
                | Q(demande__organisation_id__in=organisations)
            )
            .select_related("demande", "demande__organisation", "client", "prestataire")
            .distinct()
        )

    @action(detail=True, methods=("post",))
    def demarrer(self, request, pk=None):
        collaboration = self.get_object()
        if collaboration.statut != Collaboration.Statut.ACCORDEE:
            raise ConflitEtat("Seule une collaboration accordée peut démarrer.")
        collaboration.statut = Collaboration.Statut.EN_COURS
        collaboration.save(update_fields=("statut",))
        return Response(self.get_serializer(collaboration).data)

    @action(detail=True, methods=("post",), url_path="confirmer-terminaison")
    @transaction.atomic
    def confirmer_terminaison(self, request, pk=None):
        collaboration = (
            self.get_queryset()
            .select_for_update()
            .filter(pk=pk)
            .first()
        )
        if collaboration is None:
            raise exceptions.NotFound()
        if collaboration.statut not in (
            Collaboration.Statut.ACCORDEE,
            Collaboration.Statut.EN_COURS,
        ):
            raise ConflitEtat("Cette collaboration est déjà terminée.")
        if collaboration.prestataire_id == request.user.pk:
            collaboration.prestataire_a_confirme_fin = True
        elif represente_client_collaboration(collaboration, request.user):
            collaboration.client_a_confirme_fin = True
        else:
            raise exceptions.PermissionDenied()
        champs = ["client_a_confirme_fin", "prestataire_a_confirme_fin"]
        if (
            collaboration.client_a_confirme_fin
            and collaboration.prestataire_a_confirme_fin
        ):
            collaboration.statut = Collaboration.Statut.TERMINEE
            collaboration.terminee_le = timezone.now()
            champs.extend(("statut", "terminee_le"))
        collaboration.save(update_fields=champs)
        return Response(self.get_serializer(collaboration).data)


class JalonVueSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JalonSerializer

    def get_queryset(self):
        return Jalon.objects.filter(
            Q(collaboration__client=self.request.user)
            | Q(collaboration__prestataire=self.request.user)
        ).select_related("collaboration")


class LivrableVueSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LivrableSerializer

    def get_queryset(self):
        return Livrable.objects.filter(
            Q(jalon__collaboration__client=self.request.user)
            | Q(jalon__collaboration__prestataire=self.request.user)
        ).select_related("jalon__collaboration", "auteur")
