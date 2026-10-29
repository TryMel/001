from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from opportunites.models import Candidature, Opportunite
from notifications.models import Notification

from .models import Conversation, Message

Utilisateur = get_user_model()


class MessagerieTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.candidat = Utilisateur.objects.create_user(
            username="candidat@akasha.ci",
            email="candidat@akasha.ci",
            password="test-password-for-message-tests",
        )
        self.recruteur = Utilisateur.objects.create_user(
            username="recruteur@akasha.ci",
            email="recruteur@akasha.ci",
            password="test-password-for-message-tests",
        )
        self.autre = Utilisateur.objects.create_user(
            username="autre@akasha.ci",
            email="autre@akasha.ci",
            password="test-password-for-message-tests",
        )
        self.offre = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Développeur",
            description="Offre publiée.",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
        )
        self.candidature = Candidature.objects.create(
            opportunite=self.offre,
            candidat=self.candidat,
            message="Ma candidature.",
        )

    def test_conversation_liee_a_une_candidature_et_limitee_aux_participants(self):
        self.client.force_authenticate(user=self.candidat)
        creation = self.client.post(
            "/api/messagerie/conversations/",
            {"candidature": self.candidature.pk},
            format="json",
        )

        self.assertEqual(creation.status_code, status.HTTP_201_CREATED)
        conversation = Conversation.objects.get(candidature=self.candidature)
        self.assertSetEqual(
            set(conversation.participants.values_list("pk", flat=True)),
            {self.candidat.pk, self.recruteur.pk},
        )

        self.client.force_authenticate(user=self.autre)
        liste = self.client.get("/api/messagerie/conversations/")
        detail = self.client.get(
            f"/api/messagerie/conversations/{conversation.pk}/"
        )
        self.assertEqual(liste.data["results"], [])
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_message_idempotent_et_non_modifiable_par_un_participant(self):
        conversation = Conversation.objects.create(candidature=self.candidature)
        conversation.participants.add(self.candidat, self.recruteur)
        self.client.force_authenticate(user=self.candidat)

        contenu = {
            "conversation": conversation.pk,
            "contenu": "Bonjour, merci pour votre retour.",
            "client_message_id": "mobile-msg-001",
        }
        premier = self.client.post(
            "/api/messagerie/messages/",
            contenu,
            format="json",
        )
        second = self.client.post(
            "/api/messagerie/messages/",
            contenu,
            format="json",
        )

        self.assertEqual(premier.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(premier.data["id"], second.data["id"])
        self.assertEqual(Message.objects.filter(conversation=conversation).count(), 1)
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.recruteur,
                titre="Nouveau message",
            ).exists()
        )

        self.client.force_authenticate(user=self.recruteur)
        modification = self.client.patch(
            f"/api/messagerie/messages/{premier.data['id']}/",
            {"contenu": "Contenu modifié."},
            format="json",
        )
        self.assertEqual(modification.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
