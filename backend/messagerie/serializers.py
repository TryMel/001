from rest_framework import serializers

from .models import Conversation, Message
from opportunites.models import Candidature


class MessageSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(source="auteur.get_full_name", read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "auteur",
            "auteur_nom",
            "contenu",
            "client_message_id",
            "lu_le",
            "cree_le",
        )
        read_only_fields = ("auteur", "auteur_nom", "lu_le", "cree_le")

    def validate_conversation(self, conversation):
        utilisateur = self.context["request"].user
        if not conversation.participants.filter(pk=utilisateur.pk).exists():
            raise serializers.ValidationError("Vous ne participez pas à cette conversation.")
        if not conversation.candidature_id:
            raise serializers.ValidationError(
                "Cette conversation n’est pas rattachée à une candidature."
            )
        return conversation


class ConversationSerializer(serializers.ModelSerializer):
    candidature = serializers.PrimaryKeyRelatedField(
        queryset=Candidature.objects.select_related("opportunite", "candidat").all(),
    )

    class Meta:
        model = Conversation
        fields = ("id", "candidature", "participants", "cree_le")
        read_only_fields = ("id", "participants", "cree_le")

    def validate_candidature(self, candidature):
        utilisateur = self.context["request"].user
        if utilisateur.pk not in (
            candidature.candidat_id,
            candidature.opportunite.createur_id,
        ):
            raise serializers.ValidationError(
                "Seuls le candidat et le recruteur concernés peuvent ouvrir l’échange."
            )
        return candidature
