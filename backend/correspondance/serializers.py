from rest_framework import serializers

from profils.serializers import ProfilSerializer


class RechercheProfilsQuerySerializer(serializers.Serializer):
    competence = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        max_length=20,
    )
    ville = serializers.CharField(required=False, allow_blank=True, max_length=100)
    disponible = serializers.BooleanField(required=False, default=None, allow_null=True)


class ExplicationCorrespondanceSerializer(serializers.Serializer):
    competences_correspondantes = serializers.IntegerField()
    competences_demandees = serializers.IntegerField()
    couverture_pourcent = serializers.IntegerField()
    disponible = serializers.BooleanField()
    identite_verifiee = serializers.BooleanField()


class ResultatRechercheProfilsSerializer(serializers.Serializer):
    profil = ProfilSerializer()
    score = serializers.IntegerField()
    explication = ExplicationCorrespondanceSerializer()
