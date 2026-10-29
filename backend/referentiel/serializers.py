from rest_framework import serializers
from .models import Competence, Metier

class MetierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metier
        fields = (
            "id",
            "code",
            "nom",
            "parent",
            "classification_source",
            "code_source",
            "version_source",
            "url_source",
            "licence_source",
        )
        read_only_fields = fields

class CompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competence
        fields = (
            "id",
            "nom",
            "metiers",
            "classification_source",
            "code_source",
            "version_source",
            "url_source",
            "licence_source",
        )
        read_only_fields = fields
