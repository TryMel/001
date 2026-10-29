from django.db import transaction
from rest_framework import serializers
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from configuration.medias import compresser_image, supprimer_ancienne_image
from medias.serializers import ImagesUrlMixin
from referentiel.models import Competence
from portfolios.models import Experience, Formation, Qualification, Realisation
from .models import (
    CreneauHebdomadaire,
    DisponibiliteProfil,
    ExceptionDisponibilite,
    NiveauCompetence,
    ProfilProfessionnel,
)


class NiveauCompetenceSerializer(serializers.ModelSerializer):
    competence_nom = serializers.SerializerMethodField()
    est_personnalisee = serializers.SerializerMethodField()

    def get_competence_nom(self, niveau):
        if niveau.competence_id:
            return niveau.competence.nom
        return niveau.competence_personnalisee

    def get_est_personnalisee(self, niveau):
        return niveau.competence_id is None

    class Meta:
        model = NiveauCompetence
        fields = (
            "competence",
            "competence_personnalisee",
            "competence_nom",
            "est_personnalisee",
            "niveau",
            "preuve",
        )
        read_only_fields = ("competence_nom",)


class NiveauCompetenceEcritureSerializer(serializers.Serializer):
    competence = serializers.PrimaryKeyRelatedField(
        queryset=Competence.objects.all(),
        required=False,
        allow_null=True,
    )
    competence_personnalisee = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )
    niveau = serializers.ChoiceField(
        choices=NiveauCompetence.Niveau.choices,
        required=False,
        default=NiveauCompetence.Niveau.AUTONOME,
    )
    preuve = serializers.URLField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        competence = attrs.get("competence")
        nom_personnalise = attrs.get("competence_personnalisee", "").strip()
        if bool(competence) == bool(nom_personnalise):
            raise serializers.ValidationError(
                "Choisissez une compétence du référentiel ou saisissez une compétence personnalisée."
            )
        attrs["competence_personnalisee"] = nom_personnalise
        return attrs


class ProfilSerializer(serializers.ModelSerializer):
    competences_detail = NiveauCompetenceSerializer(
        source="niveaucompetence_set", many=True, read_only=True
    )
    competences = NiveauCompetenceEcritureSerializer(
        many=True, write_only=True, required=False
    )
    metier_nom = serializers.CharField(source="metier.nom", read_only=True)
    photo = serializers.ImageField(
        required=False, allow_null=True, write_only=True
    )
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = ProfilProfessionnel
        fields = (
            "id",
            "titre",
            "biographie",
            "ville",
            "photo",
            "photo_url",
            "disponible",
            "visible_publiquement",
            "metier",
            "metier_nom",
            "competences",
            "competences_detail",
        )
        read_only_fields = ("id",)

    def validate_photo(self, photo):
        return compresser_image(photo)

    def get_photo_url(self, profil):
        if not profil.photo:
            return None
        url = profil.photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def validate_competences(self, competences):
        identifiants = [
            item["competence"].pk
            for item in competences
            if item.get("competence") is not None
        ]
        noms_personnalises = [
            item["competence_personnalisee"].casefold()
            for item in competences
            if item.get("competence_personnalisee")
        ]
        if (
            len(identifiants) != len(set(identifiants))
            or len(noms_personnalises) != len(set(noms_personnalises))
        ):
            raise serializers.ValidationError(
                "Une compétence ne peut être ajoutée qu’une seule fois."
            )
        return competences

    def validate(self, attrs):
        attrs = super().validate(attrs)
        metier = attrs.get("metier", getattr(self.instance, "metier", None))
        competences = attrs.get("competences")
        if metier and competences is not None:
            incompatibles = [
                item["competence"].nom
                for item in competences
                if item.get("competence") is not None
                if item["competence"].metiers.exists()
                and not item["competence"].metiers.filter(pk=metier.pk).exists()
            ]
            if incompatibles:
                raise serializers.ValidationError(
                    {
                        "competences": (
                            "Certaines compétences ne correspondent pas au métier "
                            f"sélectionné : {', '.join(incompatibles)}."
                        )
                    }
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        competences = validated_data.pop("competences", [])
        profil = super().create(validated_data)
        self._remplacer_competences(profil, competences)
        return profil

    @transaction.atomic
    def update(self, instance, validated_data):
        remplacer_competences = "competences" in validated_data
        competences = validated_data.pop("competences", [])
        ancienne_photo = instance.photo.name if instance.photo else ""
        profil = super().update(instance, validated_data)
        supprimer_ancienne_image(profil, "photo", ancienne_photo)
        if remplacer_competences:
            self._remplacer_competences(profil, competences)
        return profil

    @staticmethod
    def _remplacer_competences(profil, competences):
        profil.niveaucompetence_set.all().delete()
        NiveauCompetence.objects.bulk_create(
            [
                NiveauCompetence(profil=profil, **competence)
                for competence in competences
            ]
        )


class CompetencePubliqueSerializer(serializers.ModelSerializer):
    competence_nom = serializers.SerializerMethodField()
    est_personnalisee = serializers.SerializerMethodField()

    def get_competence_nom(self, niveau):
        if niveau.competence_id:
            return niveau.competence.nom
        return niveau.competence_personnalisee

    def get_est_personnalisee(self, niveau):
        return niveau.competence_id is None

    class Meta:
        model = NiveauCompetence
        fields = ("competence_nom", "est_personnalisee", "niveau")


class ExperiencePubliqueSerializer(serializers.ModelSerializer):
    entreprise_reference_statut_verification = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = (
            "organisation",
            "poste",
            "description",
            "debut",
            "fin",
            "est_attestee",
            "entreprise_reference_statut_verification",
        )

    def get_entreprise_reference_statut_verification(self, experience):
        if experience.entreprise_reference_id:
            return experience.entreprise_reference.statut_verification
        return None


class FormationPubliqueSerializer(serializers.ModelSerializer):
    etablissement_reference_statut_verification = serializers.SerializerMethodField()
    programme_reference_statut_verification = serializers.SerializerMethodField()

    class Meta:
        model = Formation
        fields = (
            "etablissement",
            "intitule",
            "debut",
            "fin",
            "est_verifiee",
            "etablissement_reference_statut_verification",
            "programme_reference_statut_verification",
        )

    def get_etablissement_reference_statut_verification(self, formation):
        if formation.etablissement_reference_id:
            return formation.etablissement_reference.statut_verification
        return None

    def get_programme_reference_statut_verification(self, formation):
        if formation.programme_reference_id:
            return formation.programme_reference.statut_verification
        return None


class RealisationPubliqueSerializer(ImagesUrlMixin):
    images_url = serializers.SerializerMethodField()

    class Meta:
        model = Realisation
        fields = (
            "titre",
            "description",
            "lien",
            "date_realisation",
            "est_verifiee",
            "images_url",
        )


class QualificationPubliqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = ("nom", "organisme", "expiration", "est_confirmee")


class ProfilPublicSerializer(serializers.ModelSerializer):
    nom = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    metier_nom = serializers.CharField(source="metier.nom", read_only=True)
    competences = CompetencePubliqueSerializer(
        source="niveaucompetence_set", many=True, read_only=True
    )
    experiences = ExperiencePubliqueSerializer(many=True, read_only=True)
    formations = FormationPubliqueSerializer(many=True, read_only=True)
    realisations = RealisationPubliqueSerializer(many=True, read_only=True)
    qualifications = QualificationPubliqueSerializer(many=True, read_only=True)

    class Meta:
        model = ProfilProfessionnel
        fields = (
            "id",
            "nom",
            "photo_url",
            "titre",
            "biographie",
            "ville",
            "disponible",
            "metier_nom",
            "competences",
            "experiences",
            "formations",
            "realisations",
            "qualifications",
        )

    def get_nom(self, profil):
        return profil.utilisateur.get_full_name().strip()

    def get_photo_url(self, profil):
        if not profil.photo:
            return None
        url = profil.photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class CreneauHebdomadaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreneauHebdomadaire
        fields = ("id", "jour", "debut", "fin")
        read_only_fields = ("id",)

    def validate(self, attrs):
        debut = attrs.get("debut", getattr(self.instance, "debut", None))
        fin = attrs.get("fin", getattr(self.instance, "fin", None))
        if debut is not None and fin is not None and debut >= fin:
            raise serializers.ValidationError(
                {"fin": "L’heure de fin doit être après l’heure de début."}
            )
        return attrs


class ExceptionDisponibiliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExceptionDisponibilite
        fields = ("date", "est_disponible", "debut", "fin")

    def validate(self, attrs):
        est_disponible = attrs.get("est_disponible", False)
        debut = attrs.get("debut")
        fin = attrs.get("fin")
        if est_disponible and (debut is None or fin is None or debut >= fin):
            raise serializers.ValidationError(
                "Une disponibilité exceptionnelle exige un horaire valide."
            )
        if not est_disponible and (debut is not None or fin is not None):
            raise serializers.ValidationError(
                "Une indisponibilité exceptionnelle ne doit pas contenir d’horaire."
            )
        return attrs


class DisponibiliteProfilSerializer(serializers.ModelSerializer):
    creneaux = CreneauHebdomadaireSerializer(many=True, required=False)
    exceptions = ExceptionDisponibiliteSerializer(many=True, required=False)

    class Meta:
        model = DisponibiliteProfil
        fields = ("fuseau", "creneaux", "exceptions", "modifie_le")
        read_only_fields = ("modifie_le",)

    def validate_fuseau(self, fuseau):
        try:
            ZoneInfo(fuseau)
        except (ZoneInfoNotFoundError, ValueError) as erreur:
            raise serializers.ValidationError(
                "Choisissez un fuseau horaire reconnu."
            ) from erreur
        return fuseau

    def validate_creneaux(self, creneaux):
        horaires = {}
        for creneau in creneaux:
            jour = creneau["jour"]
            horaires.setdefault(jour, []).append((creneau["debut"], creneau["fin"]))
        for jour, intervalles in horaires.items():
            intervalles.sort()
            if any(
                courant[0] < precedent[1]
                for precedent, courant in zip(intervalles, intervalles[1:])
            ):
                raise serializers.ValidationError(
                    f"Les créneaux du jour {jour} ne peuvent pas se chevaucher."
                )
        return creneaux

    def validate_exceptions(self, exceptions):
        dates = [exception["date"] for exception in exceptions]
        if len(dates) != len(set(dates)):
            raise serializers.ValidationError(
                "Une date ne peut avoir qu’une exception de disponibilité."
            )
        return exceptions

    @transaction.atomic
    def update(self, instance, validated_data):
        creneaux = validated_data.pop("creneaux", None)
        exceptions = validated_data.pop("exceptions", None)
        disponibilite = super().update(instance, validated_data)
        if creneaux is not None:
            disponibilite.creneaux.all().delete()
            CreneauHebdomadaire.objects.bulk_create(
                [
                    CreneauHebdomadaire(disponibilite=disponibilite, **creneau)
                    for creneau in creneaux
                ]
            )
        if exceptions is not None:
            disponibilite.exceptions.all().delete()
            ExceptionDisponibilite.objects.bulk_create(
                [
                    ExceptionDisponibilite(
                        disponibilite=disponibilite,
                        **exception,
                    )
                    for exception in exceptions
                ]
            )
        return disponibilite
