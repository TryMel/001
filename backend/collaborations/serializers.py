from rest_framework import serializers

from configuration.medias import compresser_image, supprimer_ancienne_image
from organisations.models import AppartenanceOrganisation
from profils.models import ProfilProfessionnel
from referentiel.models import Competence

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
    peut_proposer,
    represente_client_collaboration,
    utilisateur_a_role,
)
from medias.serializers import GalerieImagesMixin


def valider_photo(photo):
    return compresser_image(photo)


def valider_nombre_total_images(serializer, attrs):
    images = attrs.get("images")
    if images is not None:
        nombre_images = len(images)
    elif serializer.instance:
        nombre_images = serializer.instance.images.count()
    else:
        nombre_images = 0
    photo = attrs.get(
        "photo",
        getattr(serializer.instance, "photo", None),
    )
    if photo:
        nombre_images += 1
    if nombre_images > 5:
        raise serializers.ValidationError(
            {"images": "Ajoutez cinq images au maximum, photo principale comprise."}
        )


class OffreServiceSerializer(GalerieImagesMixin, serializers.ModelSerializer):
    prestataire_nom = serializers.CharField(
        source="profil.utilisateur.get_full_name",
        read_only=True,
    )
    metier_nom = serializers.CharField(
        source="profil.metier.nom",
        read_only=True,
        allow_null=True,
    )
    est_proprietaire = serializers.SerializerMethodField()
    photo = serializers.ImageField(
        required=False, allow_null=True, write_only=True
    )
    photo_url = serializers.SerializerMethodField()
    prestataire_photo_url = serializers.SerializerMethodField()
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True,
        max_length=5,
    )
    images_url = serializers.SerializerMethodField()

    class Meta:
        model = OffreService
        fields = (
            "id",
            "titre",
            "description",
            "ville",
            "pays",
            "photo",
            "photo_url",
            "images",
            "images_url",
            "prestataire_photo_url",
            "tarification",
            "prix",
            "devise",
            "delai_jours",
            "statut",
            "competences",
            "prestataire_nom",
            "metier_nom",
            "est_proprietaire",
            "cree_le",
            "modifie_le",
        )
        read_only_fields = (
            "id",
            "photo_url",
            "prestataire_photo_url",
            "statut",
            "prestataire_nom",
            "metier_nom",
            "cree_le",
            "modifie_le",
        )

    def validate_photo(self, photo):
        return valider_photo(photo)

    def get_photo_url(self, offre):
        return self._url_photo(offre.photo)

    def get_prestataire_photo_url(self, offre):
        return self._url_photo(offre.profil.photo)

    def _url_photo(self, photo):
        if not photo:
            return None
        url = photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def validate_delai_jours(self, valeur):
        if valeur is not None and not 1 <= valeur <= 3650:
            raise serializers.ValidationError(
                "Le délai doit être compris entre 1 et 3 650 jours."
            )
        return valeur

    def validate(self, attrs):
        utilisateur = self.context["request"].user
        if "statut" in self.initial_data:
            raise serializers.ValidationError(
                {"statut": "Utilisez l’action de publication ou de fermeture."}
            )
        if self.instance is None and not peut_proposer(utilisateur):
            raise serializers.ValidationError(
                "Un profil professionnel actif est requis pour publier un service."
            )
        tarification = attrs.get(
            "tarification",
            getattr(self.instance, "tarification", OffreService.Tarification.SUR_DEVIS),
        )
        prix = attrs.get("prix", getattr(self.instance, "prix", None))
        if tarification == OffreService.Tarification.FORFAIT and prix is None:
            raise serializers.ValidationError(
                {"prix": "Un prix est requis pour une tarification au forfait."}
            )
        if tarification == OffreService.Tarification.SUR_DEVIS and prix is not None:
            raise serializers.ValidationError(
                {"prix": "Laissez le prix vide pour une prestation sur devis."}
            )
        devise = attrs.get("devise", getattr(self.instance, "devise", "XOF"))
        if devise != "XOF":
            raise serializers.ValidationError(
                {"devise": "Le marché initial accepte uniquement le XOF."}
            )
        if self.instance and self.instance.profil.utilisateur_id != self.context[
            "request"
        ].user.pk:
            raise serializers.ValidationError("Cette offre ne vous appartient pas.")
        valider_nombre_total_images(self, attrs)
        return attrs

    def get_est_proprietaire(self, offre):
        utilisateur = self.context["request"].user
        return (
            utilisateur.is_authenticated
            and offre.profil.utilisateur_id == utilisateur.pk
        )

    def create(self, validated_data):
        competences = validated_data.pop("competences", [])
        images = validated_data.pop("images", [])
        profil, _ = ProfilProfessionnel.objects.get_or_create(
            utilisateur=self.context["request"].user
        )
        offre = OffreService.objects.create(profil=profil, **validated_data)
        offre.competences.set(competences)
        self._remplacer_images(offre, images)
        return offre

    def update(self, instance, validated_data):
        competences = validated_data.pop("competences", None)
        remplacer_images = "images" in validated_data
        images = validated_data.pop("images", [])
        ancienne_photo = instance.photo.name if instance.photo else ""
        offre = super().update(instance, validated_data)
        supprimer_ancienne_image(offre, "photo", ancienne_photo)
        if competences is not None:
            offre.competences.set(competences)
        if remplacer_images:
            self._remplacer_images(offre, images)
        return offre


class DemandeServiceSerializer(GalerieImagesMixin, serializers.ModelSerializer):
    organisation_nom = serializers.CharField(
        source="organisation.nom",
        read_only=True,
        allow_null=True,
    )
    competences = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Competence.objects.all(),
        required=False,
    )
    est_gestionnaire = serializers.SerializerMethodField()
    photo = serializers.ImageField(
        required=False, allow_null=True, write_only=True
    )
    photo_url = serializers.SerializerMethodField()
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True,
        max_length=5,
    )
    images_url = serializers.SerializerMethodField()

    class Meta:
        model = DemandeService
        fields = (
            "id",
            "organisation",
            "organisation_nom",
            "est_gestionnaire",
            "titre",
            "description",
            "ville",
            "pays",
            "photo",
            "photo_url",
            "images",
            "images_url",
            "budget_minimum",
            "budget_maximum",
            "devise",
            "visibilite",
            "statut",
            "competences",
            "cree_le",
            "publie_le",
            "modifie_le",
        )
        read_only_fields = (
            "id",
            "organisation_nom",
            "photo_url",
            "statut",
            "cree_le",
            "publie_le",
            "modifie_le",
        )

    def validate_photo(self, photo):
        return valider_photo(photo)

    def get_photo_url(self, demande):
        if not demande.photo:
            return None
        url = demande.photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def validate(self, attrs):
        utilisateur = self.context["request"].user
        if "statut" in self.initial_data:
            raise serializers.ValidationError(
                {"statut": "Utilisez l’action de publication ou de fermeture."}
            )
        minimum = attrs.get(
            "budget_minimum",
            getattr(self.instance, "budget_minimum", None),
        )
        maximum = attrs.get(
            "budget_maximum",
            getattr(self.instance, "budget_maximum", None),
        )
        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError(
                {"budget_maximum": "Le maximum doit être supérieur ou égal au minimum."}
            )
        devise = attrs.get("devise", getattr(self.instance, "devise", "XOF"))
        if devise != "XOF":
            raise serializers.ValidationError(
                {"devise": "Le marché initial accepte uniquement le XOF."}
            )
        organisation = attrs.get(
            "organisation",
            getattr(self.instance, "organisation", None),
        )
        if (
            self.instance is None
            and organisation is None
            and not utilisateur_a_role(utilisateur, "client")
        ):
            raise serializers.ValidationError(
                "Attribuez le rôle client pour publier une demande personnelle."
            )
        if organisation is not None and not AppartenanceOrganisation.objects.filter(
            organisation=organisation,
            utilisateur=self.context["request"].user,
            role__in=(
                AppartenanceOrganisation.Role.PROPRIETAIRE,
                AppartenanceOrganisation.Role.GESTIONNAIRE,
            ),
        ).exists():
            raise serializers.ValidationError(
                {"organisation": "Une permission de gestion active est requise."}
            )
        if self.instance and not peut_gerer_demande(
            self.instance, self.context["request"].user
        ):
            raise serializers.ValidationError("Cette demande ne vous appartient pas.")
        if (
            self.instance
            and self.instance.propositions.exclude(
                statut=Proposition.Statut.RETIREE
            ).exists()
        ):
            raise serializers.ValidationError(
                "Une demande ayant reçu une proposition ne peut plus être modifiée."
            )
        valider_nombre_total_images(self, attrs)
        return attrs

    def get_est_gestionnaire(self, demande):
        return peut_gerer_demande(demande, self.context["request"].user)

    def create(self, validated_data):
        competences = validated_data.pop("competences", [])
        images = validated_data.pop("images", [])
        demande = DemandeService.objects.create(
            client=self.context["request"].user,
            **validated_data,
        )
        demande.competences.set(competences)
        self._remplacer_images(demande, images)
        return demande

    def update(self, instance, validated_data):
        competences = validated_data.pop("competences", None)
        remplacer_images = "images" in validated_data
        images = validated_data.pop("images", [])
        ancienne_photo = instance.photo.name if instance.photo else ""
        demande = super().update(instance, validated_data)
        supprimer_ancienne_image(demande, "photo", ancienne_photo)
        if competences is not None:
            demande.competences.set(competences)
        if remplacer_images:
            self._remplacer_images(demande, images)
        return demande


class PropositionCreationSerializer(serializers.Serializer):
    montant = serializers.IntegerField(min_value=0)
    devise = serializers.CharField(max_length=3, default="XOF")
    delai_jours = serializers.IntegerField(min_value=1, max_value=3650)
    message = serializers.CharField(max_length=2000)


class PropositionSerializer(serializers.ModelSerializer):
    prestataire_nom = serializers.CharField(
        source="prestataire.get_full_name",
        read_only=True,
    )
    expected_version = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=1,
    )
    est_auteur = serializers.SerializerMethodField()
    peut_accepter = serializers.SerializerMethodField()

    class Meta:
        model = Proposition
        fields = (
            "id",
            "demande",
            "prestataire",
            "prestataire_nom",
            "est_auteur",
            "peut_accepter",
            "montant",
            "devise",
            "delai_jours",
            "message",
            "statut",
            "version",
            "expected_version",
            "cree_le",
            "modifie_le",
        )
        read_only_fields = (
            "id",
            "demande",
            "prestataire",
            "prestataire_nom",
            "statut",
            "version",
            "cree_le",
            "modifie_le",
        )

    def validate(self, attrs):
        proposition = self.instance
        if proposition is None:
            return attrs
        if proposition.prestataire_id != self.context["request"].user.pk:
            raise serializers.ValidationError("Cette proposition ne vous appartient pas.")
        if proposition.statut != Proposition.Statut.SOUMISE:
            raise serializers.ValidationError(
                "Seule une proposition en attente peut être modifiée."
            )
        if attrs.get("expected_version") != proposition.version:
            raise serializers.ValidationError(
                {"expected_version": "La proposition a été modifiée. Rechargez-la."}
            )
        if "statut" in self.initial_data:
            raise serializers.ValidationError(
                {"statut": "Utilisez les actions d’acceptation ou de retrait."}
            )
        return attrs

    def get_est_auteur(self, proposition):
        return proposition.prestataire_id == self.context["request"].user.pk

    def get_peut_accepter(self, proposition):
        return peut_gerer_demande(
            proposition.demande,
            self.context["request"].user,
        )

    def update(self, instance, validated_data):
        validated_data.pop("expected_version", None)
        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)


class CollaborationSerializer(serializers.ModelSerializer):
    demande_titre = serializers.CharField(source="demande.titre", read_only=True)
    autre_partie_nom = serializers.SerializerMethodField()

    class Meta:
        model = Collaboration
        fields = (
            "id",
            "demande",
            "demande_titre",
            "proposition",
            "client",
            "prestataire",
            "autre_partie_nom",
            "perimetre",
            "montant",
            "devise",
            "statut",
            "client_a_confirme_fin",
            "prestataire_a_confirme_fin",
            "debut",
            "echeance",
            "cree_le",
            "terminee_le",
        )
        read_only_fields = fields

    def get_autre_partie_nom(self, collaboration):
        utilisateur = self.context["request"].user
        autre_partie = collaboration.prestataire
        if collaboration.prestataire_id == utilisateur.pk:
            autre_partie = collaboration.client
        elif not represente_client_collaboration(collaboration, utilisateur):
            autre_partie = collaboration.client
        return autre_partie.get_full_name()


class JalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jalon
        fields = (
            "id",
            "collaboration",
            "titre",
            "description",
            "echeance",
            "statut",
            "ordre",
        )
        read_only_fields = ("id", "collaboration", "statut")

    def validate(self, attrs):
        if self.instance and self.instance.statut == Jalon.Statut.VALIDE:
            raise serializers.ValidationError("Un jalon validé ne peut plus être modifié.")
        return attrs


class LivrableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livrable
        fields = (
            "id",
            "jalon",
            "auteur",
            "titre",
            "lien",
            "commentaire",
            "est_valide",
            "cree_le",
        )
        read_only_fields = ("id", "auteur", "est_valide", "cree_le")

    def validate_jalon(self, jalon):
        utilisateur = self.context["request"].user
        if not jalon.collaboration_id or not (
            jalon.collaboration.client_id == utilisateur.pk
            or jalon.collaboration.prestataire_id == utilisateur.pk
        ):
            raise serializers.ValidationError("Ce jalon ne vous est pas accessible.")
        if jalon.collaboration.statut == Collaboration.Statut.TERMINEE:
            raise serializers.ValidationError(
                "Un livrable ne peut plus être ajouté après la fin de la collaboration."
            )
        return jalon

    def create(self, validated_data):
        return Livrable.objects.create(
            auteur=self.context["request"].user,
            **validated_data,
        )
