from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from comptes.roles import utilisateur_a_role
from medias.serializers import GalerieImagesMixin
from organisations.models import Organisation
from django.utils import timezone
from profils.models import ProfilProfessionnel
from profils.serializers import ProfilPublicSerializer
from referentiel.models import Competence
from .models import Candidature, HistoriqueCandidature, Opportunite
from .permissions import peut_gerer_organisation_recrutement


class FiltresOpportuniteSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(
        choices=Opportunite.Statut.choices,
        required=False,
    )
    type = serializers.ChoiceField(choices=Opportunite.Type.choices, required=False)
    contrat = serializers.ChoiceField(
        choices=Opportunite.Contrat.choices,
        required=False,
    )
    ville = serializers.CharField(max_length=100, required=False)
    pays = serializers.RegexField(r"^[A-Za-z]{2}$", required=False)
    devise = serializers.RegexField(r"^[A-Za-z]{3}$", required=False)
    metier = serializers.IntegerField(min_value=1, required=False)
    competence = serializers.IntegerField(min_value=1, required=False)
    budget_min = serializers.IntegerField(min_value=0, required=False)
    budget_max = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):
        minimum = attrs.get("budget_min")
        maximum = attrs.get("budget_max")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError(
                {"budget_max": "Le budget maximum doit être supérieur au minimum."}
            )
        if (minimum is not None or maximum is not None) and "devise" not in attrs:
            raise serializers.ValidationError(
                {"devise": "Sélectionnez une devise pour filtrer les budgets."}
            )
        return attrs


class CompetenceOpportuniteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competence
        fields = ("id", "nom")


class OpportuniteSerializer(GalerieImagesMixin, serializers.ModelSerializer):
    createur_nom = serializers.CharField(source="createur.get_full_name", read_only=True)
    organisation_nom = serializers.CharField(
        source="organisation.nom",
        read_only=True,
        allow_null=True,
    )
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all(),
        required=False,
        allow_null=True,
    )
    metier_nom = serializers.CharField(
        source="metier.nom",
        read_only=True,
        allow_null=True,
    )
    competences_detail = CompetenceOpportuniteSerializer(
        source="competences",
        many=True,
        read_only=True,
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True,
        max_length=5,
    )
    images_url = serializers.SerializerMethodField()

    class Meta:
        model = Opportunite
        fields = (
            "id",
            "titre",
            "description",
            "organisation",
            "organisation_nom",
            "type",
            "statut",
            "ville",
            "pays",
            "budget_minimum",
            "budget_maximum",
            "devise",
            "contrat",
            "niveau_etudes",
            "duree",
            "livrables",
            "urgence",
            "motif_urgence",
            "date_limite_candidature",
            "metier",
            "metier_nom",
            "competences",
            "competences_detail",
            "images",
            "images_url",
            "createur",
            "createur_nom",
            "cree_le",
        )
        read_only_fields = ("createur", "organisation_nom", "statut", "cree_le")

    def validate_organisation(self, organisation):
        if organisation is not None and not peut_gerer_organisation_recrutement(
            organisation,
            self.context["request"].user,
        ):
            raise PermissionDenied(
                "Vous devez être propriétaire ou recruteur de cette organisation."
            )
        return organisation

    def validate(self, attrs):
        utilisateur = self.context["request"].user
        organisation = attrs.get(
            "organisation",
            getattr(self.instance, "organisation", None),
        )
        if self.instance is None:
            if organisation is None and not utilisateur_a_role(
                utilisateur,
                "recruteur",
            ):
                raise PermissionDenied(
                    "Attribuez le rôle recruteur ou choisissez une organisation autorisée."
                )
        elif (
            "organisation" in self.initial_data
            and attrs.get("organisation") != self.instance.organisation
        ):
            raise serializers.ValidationError(
                {"organisation": "L'organisation d'une offre existante ne peut pas changer."}
            )
        budget_minimum = attrs.get(
            "budget_minimum",
            getattr(self.instance, "budget_minimum", None),
        )
        budget_maximum = attrs.get(
            "budget_maximum",
            getattr(self.instance, "budget_maximum", None),
        )
        if (
            budget_minimum is not None
            and budget_maximum is not None
            and budget_minimum > budget_maximum
        ):
            raise serializers.ValidationError(
                {"budget_maximum": "Le budget maximum doit être supérieur au minimum."}
            )
        urgence = attrs.get(
            "urgence",
            getattr(self.instance, "urgence", Opportunite.Urgence.NORMALE),
        )
        motif_urgence = attrs.get(
            "motif_urgence",
            getattr(self.instance, "motif_urgence", ""),
        ).strip()
        if urgence == Opportunite.Urgence.URGENTE and not motif_urgence:
            raise serializers.ValidationError(
                {"motif_urgence": "Expliquez pourquoi ce besoin est urgent."}
            )
        date_limite = attrs.get(
            "date_limite_candidature",
            getattr(self.instance, "date_limite_candidature", None),
        )
        if date_limite and date_limite < timezone.localdate():
            raise serializers.ValidationError(
                {"date_limite_candidature": "La date limite ne peut pas être passée."}
            )
        return attrs

    def create(self, validated_data):
        competences = validated_data.pop("competences", [])
        images = validated_data.pop("images", [])
        opportunite = Opportunite.objects.create(
            createur=self.context["request"].user,
            **validated_data,
        )
        opportunite.competences.set(competences)
        self._remplacer_images(opportunite, images)
        return opportunite

    def update(self, instance, validated_data):
        competences = validated_data.pop("competences", None)
        remplacer_images = "images" in validated_data
        images = validated_data.pop("images", [])
        opportunite = super().update(instance, validated_data)
        if competences is not None:
            opportunite.competences.set(competences)
        if remplacer_images:
            self._remplacer_images(opportunite, images)
        return opportunite


class HistoriqueCandidatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueCandidature
        fields = ("statut_precedent", "nouveau_statut", "cree_le")


class CandidatureSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source="candidat.get_full_name", read_only=True)
    historique = HistoriqueCandidatureSerializer(many=True, read_only=True)
    consentement_partage_profil = serializers.BooleanField(write_only=True, required=True)
    profil_partage = serializers.SerializerMethodField()

    class Meta:
        model = Candidature
        fields = (
            "id",
            "opportunite",
            "candidat",
            "candidat_nom",
            "message",
            "consentement_partage_profil",
            "profil_partage",
            "statut",
            "version",
            "cree_le",
            "historique",
        )
        read_only_fields = (
            "candidat",
            "statut",
            "version",
            "cree_le",
            "historique",
        )

    def validate_opportunite(self, opportunite):
        utilisateur = self.context["request"].user
        if not utilisateur_a_role(utilisateur, "candidat", "etudiant"):
            raise PermissionDenied(
                "Seuls les candidats et les étudiants peuvent postuler."
            )
        if opportunite.statut != Opportunite.Statut.PUBLIEE:
            raise serializers.ValidationError("Cette opportunité n'accepte pas de candidature.")
        if opportunite.createur_id == utilisateur.pk:
            raise serializers.ValidationError("Vous ne pouvez pas candidater à votre propre offre.")
        if (
            opportunite.date_limite_candidature is not None
            and opportunite.date_limite_candidature < timezone.localdate()
        ):
            raise serializers.ValidationError("La date limite de candidature est dépassée.")
        return opportunite

    def validate_consentement_partage_profil(self, consentement):
        if not consentement:
            raise serializers.ValidationError(
                "Votre consentement est nécessaire pour transmettre votre profil au recruteur."
            )
        return consentement

    def create(self, validated_data):
        validated_data.pop("consentement_partage_profil")
        candidat = validated_data["candidat"]
        profil = (
            ProfilProfessionnel.objects.select_related("utilisateur", "metier")
            .prefetch_related(
                "niveaucompetence_set__competence",
                "experiences",
                "formations",
                "realisations__images",
                "qualifications",
            )
            .filter(utilisateur=candidat)
            .first()
        )
        if profil is None:
            snapshot = {
                "id": None,
                "nom": candidat.get_full_name().strip(),
                "photo_url": None,
                "titre": "",
                "biographie": "",
                "ville": "",
                "disponible": False,
                "metier_nom": None,
                "competences": [],
                "experiences": [],
                "formations": [],
                "realisations": [],
                "qualifications": [],
            }
        else:
            snapshot = dict(
                ProfilPublicSerializer(
                    profil,
                    context=self.context,
                ).data
            )
        validated_data["profil_partage_snapshot"] = snapshot
        validated_data["partage_profil_consenti_le"] = timezone.now()
        return super().create(validated_data)

    def get_profil_partage(self, candidature):
        view = self.context.get("view")
        if getattr(view, "action", None) != "recues":
            return None
        return candidature.profil_partage_snapshot
