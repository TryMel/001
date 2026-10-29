from django.db import IntegrityError, transaction
from rest_framework import exceptions, mixins, permissions, viewsets

from notifications.models import Notification
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationVueSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            Conversation.objects.filter(participants=self.request.user)
            .select_related("candidature")
            .distinct()
        )

    def perform_create(self, serializer):
        candidature = serializer.validated_data["candidature"]
        try:
            with transaction.atomic():
                conversation, _ = Conversation.objects.get_or_create(
                    candidature=candidature,
                )
                conversation.participants.add(
                    candidature.candidat,
                    candidature.opportunite.createur,
                )
                serializer.instance = conversation
        except IntegrityError as erreur:
            raise exceptions.APIException(
                "La conversation n’a pas pu être créée. Réessayez."
            ) from erreur


class MessageVueSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Message.objects.filter(
            conversation__participants=self.request.user,
        ).select_related("auteur", "conversation")
        conversation_id = self.request.query_params.get("conversation")
        if conversation_id is not None:
            queryset = queryset.filter(conversation_id=conversation_id)
        return queryset

    def perform_create(self, serializer):
        donnees = serializer.validated_data
        cle_client = donnees.get("client_message_id")
        conversation = donnees["conversation"]
        utilisateur = self.request.user

        try:
            with transaction.atomic():
                if cle_client:
                    message, cree = Message.objects.get_or_create(
                        auteur=utilisateur,
                        client_message_id=cle_client,
                        defaults=donnees,
                    )
                    if not cree and (
                        message.conversation_id != conversation.pk
                        or message.contenu != donnees["contenu"]
                    ):
                        raise exceptions.ValidationError(
                            {"client_message_id": "Cette clé a déjà été utilisée."}
                        )
                else:
                    message = serializer.save(auteur=utilisateur)
                    cree = True

                if cree:
                    destinataires = conversation.participants.exclude(pk=utilisateur.pk)
                    Notification.objects.bulk_create(
                        [
                            Notification(
                                utilisateur=destinataire,
                                titre="Nouveau message",
                                message="Vous avez reçu un nouveau message lié à une candidature.",
                                lien=f"/api/messagerie/conversations/{conversation.pk}/",
                            )
                            for destinataire in destinataires
                        ]
                    )
                serializer.instance = message
        except IntegrityError as erreur:
            raise exceptions.ValidationError(
                {"client_message_id": "Ce message a déjà été envoyé."}
            ) from erreur
