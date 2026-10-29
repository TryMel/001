from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from profils.models import NiveauCompetence, ProfilProfessionnel
from referentiel.models import Competence


Utilisateur = get_user_model()


class RechercheProfilsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.demandeur = Utilisateur.objects.create_user(
            username="demandeur@example.test",
            email="demandeur@example.test",
            password="MotDePasseSecurise2026!",
        )
        self.client.force_authenticate(self.demandeur)
        self.competence = Competence.objects.create(nom="Django REST")

    def creer_profil(self, email, visible, disponible, avec_competence):
        utilisateur = Utilisateur.objects.create_user(
            username=email,
            email=email,
            password="MotDePasseSecurise2026!",
            est_verifie=True,
        )
        profil = ProfilProfessionnel.objects.create(
            utilisateur=utilisateur,
            titre="Développeur",
            visible_publiquement=visible,
            disponible=disponible,
        )
        if avec_competence:
            NiveauCompetence.objects.create(
                profil=profil,
                competence=self.competence,
                niveau=NiveauCompetence.Niveau.EXPERT,
            )
        return profil

    def test_recherche_ne_retourne_que_les_profils_visibles_et_classes(self):
        meilleur = self.creer_profil("public@example.test", True, True, True)
        self.creer_profil("prive@example.test", False, True, True)
        self.creer_profil("sans-competence@example.test", True, True, False)

        reponse = self.client.get(
            "/api/correspondance/profils/",
            {"competence": self.competence.id},
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reponse.data), 2)
        self.assertEqual(reponse.data[0]["profil"]["id"], meilleur.id)
        self.assertEqual(reponse.data[0]["explication"]["couverture_pourcent"], 100)
