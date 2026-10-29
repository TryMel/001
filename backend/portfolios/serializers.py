from rest_framework import serializers

from medias.serializers import GalerieImagesMixin
from .models import Experience, Formation, Qualification, Realisation


class PossessionProfilSerializer(serializers.ModelSerializer):
    profil = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if "profil" in self.initial_data:
            raise serializers.ValidationError(
                {"profil": "Le profil est attribué automatiquement à votre compte."}
            )
        debut = attrs.get("debut", getattr(self.instance, "debut", None))
        fin = attrs.get("fin", getattr(self.instance, "fin", None))
        if debut and fin and fin < debut:
            raise serializers.ValidationError(
                {"fin": "La date de fin ne peut pas précéder la date de début."}
            )
        return attrs


class FormationSerializer(PossessionProfilSerializer):
    etablissement_reference_statut_verification = serializers.SerializerMethodField()
    programme_reference_statut_verification = serializers.SerializerMethodField()

    class Meta:
        model = Formation
        fields = "__all__"
        read_only_fields = (
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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        etablissement = attrs.get(
            "etablissement_reference",
            getattr(self.instance, "etablissement_reference", None),
        )
        programme = attrs.get(
            "programme_reference",
            getattr(self.instance, "programme_reference", None),
        )
        nom_etablissement = attrs.get(
            "etablissement",
            getattr(self.instance, "etablissement", ""),
        )
        if etablissement and nom_etablissement.strip().casefold() != etablissement.nom.casefold():
            raise serializers.ValidationError(
                {"etablissement": "Le nom doit correspondre à l'établissement référencé."}
            )
        if (
            programme
            and programme.etablissement_id
            and (etablissement is None or programme.etablissement_id != etablissement.pk)
        ):
            raise serializers.ValidationError(
                {"programme_reference": "Le programme ne correspond pas à cet établissement."}
            )
        return attrs


class ExperienceSerializer(PossessionProfilSerializer):
    entreprise_reference_statut_verification = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = (
            "est_attestee",
            "entreprise_reference_statut_verification",
        )

    def get_entreprise_reference_statut_verification(self, experience):
        if experience.entreprise_reference_id:
            return experience.entreprise_reference.statut_verification
        return None

    def validate(self, attrs):
        attrs = super().validate(attrs)
        entreprise = attrs.get(
            "entreprise_reference",
            getattr(self.instance, "entreprise_reference", None),
        )
        organisation = attrs.get(
            "organisation",
            getattr(self.instance, "organisation", ""),
        )
        if entreprise and organisation.strip().casefold() != entreprise.nom.casefold():
            raise serializers.ValidationError(
                {"organisation": "Le nom doit correspondre à l'entreprise référencée."}
            )
        return attrs


class RealisationSerializer(GalerieImagesMixin, PossessionProfilSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True,
        max_length=5,
    )
    images_url = serializers.SerializerMethodField()

    class Meta:
        model = Realisation
        fields = (
            "id",
            "profil",
            "titre",
            "description",
            "lien",
            "date_realisation",
            "est_verifiee",
            "images",
            "images_url",
        )
        read_only_fields = ("est_verifiee",)


class QualificationSerializer(PossessionProfilSerializer):
    class Meta:
        model = Qualification
        fields = "__all__"
        read_only_fields = ("est_confirmee",)
