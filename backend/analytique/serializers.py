from rest_framework import serializers

from .models import EvenementInteraction


class EvenementInteractionSerializer(serializers.Serializer):
    fonctionnalite = serializers.ChoiceField(
        choices=EvenementInteraction.Fonctionnalite.choices
    )
