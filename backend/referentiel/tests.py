from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Competence, Metier


Utilisateur = get_user_model()


class ReferentielApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        utilisateur = Utilisateur.objects.create_user(
            username="profil@example.test",
            email="profil@example.test",
            password="test-password-for-referential-tests",
        )
        self.client.force_authenticate(utilisateur)
        self.metier = Metier.objects.create(code="dev", nom="Développement")
        self.autre_metier = Metier.objects.create(code="btp", nom="BTP")
        self.competence = Competence.objects.create(nom="Python")
        self.competence.metiers.add(self.metier)
        self.competence_generique = Competence.objects.create(nom="Communication")
        self.competence_autre_metier = Competence.objects.create(nom="Maçonnerie")
        self.competence_autre_metier.metiers.add(self.autre_metier)

    def test_competences_filtrees_par_metier_incluent_les_competences_generiques(self):
        reponse = self.client.get(
            f"/api/referentiel/competences/?metier={self.metier.pk}"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        identifiants = {element["id"] for element in reponse.data["results"]}
        self.assertEqual(
            identifiants,
            {self.competence.pk, self.competence_generique.pk},
        )

    def test_identifiant_metier_invalide_est_refuse(self):
        reponse = self.client.get(
            "/api/referentiel/competences/?metier=pas-un-identifiant"
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
