from django.conf import settings
from django.db import models
from django.db.models import Q


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    candidature = models.OneToOneField(
        "opportunites.Candidature",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="conversation",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ["-cree_le"]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenu = models.TextField(max_length=4000)
    client_message_id = models.CharField(max_length=64, null=True, blank=True)
    lu_le = models.DateTimeField(null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["cree_le"]
        constraints = [
            models.UniqueConstraint(
                fields=("auteur", "client_message_id"),
                condition=Q(client_message_id__isnull=False),
                name="message_unique_client_message_id",
            )
        ]
