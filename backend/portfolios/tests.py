from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from internationalisation.models import (
    EntrepriseReference,
    EtablissementReference,
    Marche,
    ProgrammeFormationReference,
)
from profils.models import ProfilProfessionnel


Utilisateur = get_user_model()


class PortfolioApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.proprietaire = Utilisateur.objects.create_user(
            username="pro@example.test",
            email="pro@example.test",
            password="MotDePasseSecurise2026!",
            roles_professionnels=["professionnel", "client"],
            role_actif="client",
        )
        self.autre = Utilisateur.objects.create_user(
            username="autre@example.test",
            email="autre@example.test",
            password="MotDePasseSecurise2026!",
            roles_professionnels=["candidat"],
            role_actif="candidat",
        )
        self.profil = ProfilProfessionnel.objects.create(utilisateur=self.proprietaire)
        self.autre_profil = ProfilProfessionnel.objects.create(utilisateur=self.autre)
        self.client.force_authenticate(self.proprietaire)

    def test_creation_modification_suppression_des_quatre_sections(self):
        cas = (
            (
                "experiences",
                {
                    "organisation": "Atelier",
                    "poste": "Développeuse",
                    "description": "Projet web",
                    "debut": "2022-01-01",
                    "fin": "2023-01-01",
                },
            ),
            (
                "formations",
                {
                    "etablissement": "Université",
                    "intitule": "Licence",
                    "debut": "2019-01-01",
                    "fin": "2022-01-01",
                },
            ),
            (
                "realisations",
                {
                    "titre": "Portfolio",
                    "description": "Site personnel",
                    "lien": "https://example.test",
                    "date_realisation": "2023-05-01",
                },
            ),
            (
                "qualifications",
                {
                    "nom": "Certification",
                    "organisme": "Centre",
                    "reference": "REF-01",
                    "expiration": "2028-01-01",
                },
            ),
        )

        for section, donnees in cas:
            with self.subTest(section=section):
                url = f"/api/portfolios/{section}/"
                reponse = self.client.post(url, donnees, format="json")
                self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
                identifiant = reponse.data["id"]
                self.assertEqual(reponse.data["profil"], self.profil.pk)
                reponse_modification = self.client.patch(
                    f"{url}{identifiant}/",
                    {"description": "Mise à jour"} if section != "qualifications"
                    else {"reference": "REF-02"},
                    format="json",
                )
                self.assertEqual(
                    reponse_modification.status_code,
                    status.HTTP_200_OK,
                    reponse_modification.data,
                )
                reponse_suppression = self.client.delete(f"{url}{identifiant}/")
                self.assertEqual(
                    reponse_suppression.status_code, status.HTTP_204_NO_CONTENT
                )

    def test_portfolio_refuse_profil_force_et_garde_les_verifications_admin(self):
        reponse = self.client.post(
            "/api/portfolios/experiences/",
            {
                "profil": self.autre_profil.pk,
                "organisation": "Atelier",
                "poste": "Développeuse",
                "debut": "2022-01-01",
                "est_attestee": True,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.profil.experiences.exists())
        reponse = self.client.post(
            "/api/portfolios/experiences/",
            {
                "organisation": "Atelier",
                "poste": "Développeuse",
                "debut": "2022-01-01",
                "est_attestee": True,
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertFalse(reponse.data["est_attestee"])

    def test_dates_incoherentes_sont_refusees(self):
        reponse = self.client.post(
            "/api/portfolios/formations/",
            {
                "etablissement": "Université",
                "intitule": "Licence",
                "debut": "2024-01-01",
                "fin": "2023-01-01",
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fin", reponse.data["erreurs"])

    def test_un_compte_ne_peut_pas_lire_modifier_ou_supprimer_le_portfolio_d_autrui(self):
        self.client.post(
            "/api/portfolios/experiences/",
            {
                "organisation": "Atelier",
                "poste": "Développeuse",
                "debut": "2022-01-01",
            },
            format="json",
        )
        experience = self.profil.experiences.get()
        self.client.force_authenticate(self.autre)

        self.assertEqual(
            self.client.get(
                f"/api/portfolios/experiences/{experience.pk}/"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/portfolios/experiences/{experience.pk}/",
                {"poste": "Autre"},
                format="json",
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(
                f"/api/portfolios/experiences/{experience.pk}/"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_portfolio_depuis_role_etudiant_ou_candidat(self):
        self.client.force_authenticate(self.autre)
        reponse = self.client.post(
            "/api/portfolios/realisations/",
            {
                "titre": "Projet",
                "description": "Projet étudiant",
                "date_realisation": date.today().isoformat(),
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(reponse.data["profil"], self.autre_profil.pk)

    def test_experience_et_formation_affichent_le_statut_des_references(self):
        marche = Marche.objects.get(code_pays="CI", est_actif=True)
        entreprise = EntrepriseReference.objects.create(
            marche=marche,
            nom="Atelier référencé",
        )
        etablissement = EtablissementReference.objects.create(
            marche=marche,
            nom="Institut référencé",
            type=EtablissementReference.Type.ECOLE,
        )
        programme = ProgrammeFormationReference.objects.create(
            marche=marche,
            etablissement=etablissement,
            intitule="Formation technique référencée",
        )

        experience = self.client.post(
            "/api/portfolios/experiences/",
            {
                "organisation": entreprise.nom,
                "entreprise_reference": entreprise.pk,
                "poste": "Technicienne",
                "debut": "2022-01-01",
            },
            format="json",
        )
        formation = self.client.post(
            "/api/portfolios/formations/",
            {
                "etablissement": etablissement.nom,
                "etablissement_reference": etablissement.pk,
                "programme_reference": programme.pk,
                "intitule": programme.intitule,
                "debut": "2020-01-01",
            },
            format="json",
        )

        self.assertEqual(experience.status_code, status.HTTP_201_CREATED, experience.data)
        self.assertEqual(
            experience.data["entreprise_reference_statut_verification"],
            "declaree",
        )
        self.assertEqual(formation.status_code, status.HTTP_201_CREATED, formation.data)
        self.assertEqual(
            formation.data["etablissement_reference_statut_verification"],
            "declaree",
        )
        self.assertEqual(
            formation.data["programme_reference_statut_verification"],
            "declaree",
        )

    def test_role_client_seul_ne_peut_pas_creer_de_portfolio(self):
        client = Utilisateur.objects.create_user(
            username="client@example.test",
            email="client@example.test",
            password="MotDePasseSecurise2026!",
            roles_professionnels=["client"],
            role_actif="client",
        )
        self.client.force_authenticate(client)

        reponse = self.client.get("/api/portfolios/experiences/")

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ProfilProfessionnel.objects.filter(utilisateur=client).exists())
