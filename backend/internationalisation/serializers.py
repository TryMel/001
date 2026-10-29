from rest_framework import serializers
from .models import (
    EntrepriseReference,
    EtablissementReference,
    Marche,
    ProgrammeFormationReference,
    RegleMetierLocale,
    Ville,
)


class MarcheSerializer(serializers.ModelSerializer):
    class Meta: model=Marche; fields="__all__"


class RegleMetierLocaleSerializer(serializers.ModelSerializer):
    class Meta: model=RegleMetierLocale; fields="__all__"


class ReferenceLocaliseeSerializer(serializers.ModelSerializer):
    pays = serializers.SlugRelatedField(
        source="marche",
        slug_field="code_pays",
        queryset=Marche.objects.filter(est_actif=True),
    )
    cree_par = serializers.PrimaryKeyRelatedField(read_only=True)
    cree_le = serializers.DateTimeField(read_only=True)

    def validate_nom(self, valeur):
        valeur = valeur.strip()
        if not valeur:
            raise serializers.ValidationError("Indiquez un nom.")
        return valeur


class VilleSerializer(ReferenceLocaliseeSerializer):
    class Meta:
        model = Ville
        fields = ("id", "nom", "pays", "cree_par", "cree_le")
        read_only_fields = ("id", "cree_par", "cree_le")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        marche = attrs.get("marche", getattr(self.instance, "marche", None))
        nom = attrs.get("nom", getattr(self.instance, "nom", ""))
        villes = Ville.objects.filter(marche=marche, nom__iexact=nom)
        if self.instance:
            villes = villes.exclude(pk=self.instance.pk)
        if villes.exists():
            raise serializers.ValidationError(
                {"nom": "Cette ville est déjà disponible pour ce pays."}
            )
        return attrs


class EntrepriseReferenceSerializer(ReferenceLocaliseeSerializer):
    class Meta:
        model = EntrepriseReference
        fields = (
            "id",
            "nom",
            "pays",
            "forme_juridique",
            "statut_verification",
            "identifiant_registre",
            "autorite_source",
            "source_verification",
            "url_source",
            "version_source",
            "licence_source",
            "methode_verification",
            "recuperee_le",
            "validee_pour_le",
            "verifiee_le",
            "cree_par",
            "cree_le",
        )
        read_only_fields = (
            "id",
            "statut_verification",
            "identifiant_registre",
            "autorite_source",
            "source_verification",
            "url_source",
            "version_source",
            "licence_source",
            "methode_verification",
            "recuperee_le",
            "validee_pour_le",
            "verifiee_le",
            "cree_par",
            "cree_le",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        marche = attrs.get("marche", getattr(self.instance, "marche", None))
        nom = attrs.get("nom", getattr(self.instance, "nom", ""))
        entreprises = EntrepriseReference.objects.filter(
            marche=marche,
            nom__iexact=nom,
        )
        if self.instance:
            entreprises = entreprises.exclude(pk=self.instance.pk)
        if entreprises.exists():
            raise serializers.ValidationError(
                {"nom": "Cette entreprise est déjà référencée pour ce pays."}
            )
        return attrs


class EtablissementReferenceSerializer(ReferenceLocaliseeSerializer):
    class Meta:
        model = EtablissementReference
        fields = (
            "id",
            "nom",
            "pays",
            "type",
            "statut_verification",
            "identifiant_registre",
            "autorite_source",
            "source_verification",
            "url_source",
            "version_source",
            "licence_source",
            "methode_verification",
            "recuperee_le",
            "validee_pour_le",
            "verifiee_le",
            "cree_par",
            "cree_le",
        )
        read_only_fields = (
            "id",
            "statut_verification",
            "identifiant_registre",
            "autorite_source",
            "source_verification",
            "url_source",
            "version_source",
            "licence_source",
            "methode_verification",
            "recuperee_le",
            "validee_pour_le",
            "verifiee_le",
            "cree_par",
            "cree_le",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        marche = attrs.get("marche", getattr(self.instance, "marche", None))
        nom = attrs.get("nom", getattr(self.instance, "nom", ""))
        etablissements = EtablissementReference.objects.filter(
            marche=marche,
            nom__iexact=nom,
        )
        if self.instance:
            etablissements = etablissements.exclude(pk=self.instance.pk)
        if etablissements.exists():
            raise serializers.ValidationError(
                {"nom": "Cet établissement est déjà référencé pour ce pays."}
            )
        return attrs


class ProgrammeFormationReferenceSerializer(serializers.ModelSerializer):
    pays = serializers.SlugRelatedField(
        source="marche",
        slug_field="code_pays",
        queryset=Marche.objects.filter(est_actif=True),
    )
    cree_par = serializers.PrimaryKeyRelatedField(read_only=True)
    cree_le = serializers.DateTimeField(read_only=True)
    statut_verification = serializers.CharField(read_only=True)
    identifiant_registre = serializers.CharField(read_only=True)
    autorite_source = serializers.CharField(read_only=True)
    source_verification = serializers.CharField(read_only=True)
    url_source = serializers.URLField(read_only=True)
    version_source = serializers.CharField(read_only=True)
    licence_source = serializers.CharField(read_only=True)
    methode_verification = serializers.CharField(read_only=True)
    recuperee_le = serializers.DateTimeField(read_only=True)
    validee_pour_le = serializers.DateField(read_only=True)
    verifiee_le = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ProgrammeFormationReference
        fields = (
            "id",
            "intitule",
            "niveau",
            "pays",
            "etablissement",
            "metiers",
            "statut_verification",
            "identifiant_registre",
            "autorite_source",
            "source_verification",
            "url_source",
            "version_source",
            "licence_source",
            "methode_verification",
            "recuperee_le",
            "validee_pour_le",
            "verifiee_le",
            "cree_par",
            "cree_le",
        )
        read_only_fields = (
            "id",
            "statut_verification",
            "identifiant_registre",
            "autorite_source",
            "source_verification",
            "url_source",
            "version_source",
            "licence_source",
            "methode_verification",
            "recuperee_le",
            "validee_pour_le",
            "verifiee_le",
            "cree_par",
            "cree_le",
        )

    def validate_intitule(self, valeur):
        valeur = valeur.strip()
        if not valeur:
            raise serializers.ValidationError("Indiquez un intitulé de formation.")
        return valeur

    def validate(self, attrs):
        attrs = super().validate(attrs)
        marche = attrs.get("marche", getattr(self.instance, "marche", None))
        etablissement = attrs.get(
            "etablissement",
            getattr(self.instance, "etablissement", None),
        )
        intitule = attrs.get("intitule", getattr(self.instance, "intitule", ""))
        programmes = ProgrammeFormationReference.objects.filter(
            marche=marche,
            etablissement=etablissement,
            intitule__iexact=intitule,
        )
        if self.instance:
            programmes = programmes.exclude(pk=self.instance.pk)
        if programmes.exists():
            raise serializers.ValidationError(
                {"intitule": "Cette formation est déjà référencée pour cet établissement."}
            )
        if etablissement and etablissement.marche_id != marche.pk:
            raise serializers.ValidationError(
                {"etablissement": "L'établissement doit appartenir au pays sélectionné."}
            )
        return attrs
