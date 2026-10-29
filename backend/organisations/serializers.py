from rest_framework import serializers

from configuration.medias import compresser_image, supprimer_ancienne_image
from internationalisation.models import EntrepriseReference
from .models import AppartenanceOrganisation, Organisation


class OrganisationSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(
        required=False, allow_null=True, write_only=True
    )
    photo_url = serializers.SerializerMethodField()
    reference_entreprise = serializers.PrimaryKeyRelatedField(
        queryset=EntrepriseReference.objects.select_related("marche").all(),
        required=False,
        allow_null=True,
    )
    reference_entreprise_nom = serializers.CharField(
        source="reference_entreprise.nom",
        read_only=True,
        allow_null=True,
    )
    reference_entreprise_statut_verification = serializers.CharField(
        source="reference_entreprise.statut_verification",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Organisation
        fields = (
            "id",
            "nom",
            "description",
            "photo",
            "photo_url",
            "pays",
            "ville",
            "site_web",
            "reference_entreprise",
            "reference_entreprise_nom",
            "reference_entreprise_statut_verification",
            "est_verifiee",
            "cree_le",
        )
        read_only_fields = (
            "id",
            "photo_url",
            "reference_entreprise_nom",
            "reference_entreprise_statut_verification",
            "est_verifiee",
            "cree_le",
        )

    def validate_photo(self, photo):
        return compresser_image(photo)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        reference = attrs.get(
            "reference_entreprise",
            getattr(self.instance, "reference_entreprise", None),
        )
        pays = attrs.get("pays", getattr(self.instance, "pays", "CI")).upper()
        if reference and reference.marche.code_pays != pays:
            raise serializers.ValidationError(
                {"reference_entreprise": "L'entreprise référencée doit appartenir au même pays."}
            )
        return attrs

    def update(self, instance, validated_data):
        ancienne_photo = instance.photo.name if instance.photo else ""
        organisation = super().update(instance, validated_data)
        supprimer_ancienne_image(organisation, "photo", ancienne_photo)
        return organisation

    def get_photo_url(self, organisation):
        if not organisation.photo:
            return None
        url = organisation.photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class OrganisationPubliqueSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    reference_entreprise_nom = serializers.CharField(
        source="reference_entreprise.nom",
        read_only=True,
        allow_null=True,
    )
    reference_entreprise_statut_verification = serializers.CharField(
        source="reference_entreprise.statut_verification",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Organisation
        fields = (
            "id",
            "nom",
            "description",
            "pays",
            "ville",
            "site_web",
            "reference_entreprise_nom",
            "reference_entreprise_statut_verification",
            "est_verifiee",
            "photo_url",
        )

    def get_photo_url(self, organisation):
        if not organisation.photo:
            return None
        url = organisation.photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class AppartenanceOrganisationSerializer(serializers.ModelSerializer):
    organisation_nom = serializers.CharField(
        source="organisation.nom",
        read_only=True,
    )
    organisation_verifiee = serializers.BooleanField(
        source="organisation.est_verifiee",
        read_only=True,
    )
    organisation_photo_url = serializers.SerializerMethodField()
    organisation_reference_entreprise_statut = serializers.CharField(
        source="organisation.reference_entreprise.statut_verification",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AppartenanceOrganisation
        fields = (
            "id",
            "organisation",
            "organisation_nom",
            "organisation_verifiee",
            "organisation_photo_url",
            "organisation_reference_entreprise_statut",
            "utilisateur",
            "role",
        )
        read_only_fields = ("id",)

    def get_organisation_photo_url(self, appartenance):
        photo = appartenance.organisation.photo
        if not photo:
            return None
        url = photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def validate(self, attrs):
        if self.instance and "organisation" in attrs:
            raise serializers.ValidationError(
                {"organisation": "Une adhésion ne peut pas changer d'organisation."}
            )
        return attrs
