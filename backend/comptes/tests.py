from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.test import APIClient

Utilisateur = get_user_model()


class ComptesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.donnees_inscription = {
            "first_name": "Marc",
            "last_name": "Kouassi",
            "email": "marc.kouassi@akasha.ci",
            "password": "MotDePasseSecurise2026!",
            "conditions_acceptees": True,
        }

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_inscription_et_jetons_et_verification_email(self):
        reponse = self.client.post(
            "/api/comptes/inscription/",
            self.donnees_inscription,
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", reponse.data)
        self.assertIn("refresh", reponse.data)
        self.assertEqual(reponse.data["utilisateur"]["email"], "marc.kouassi@akasha.ci")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("akasha://verification?token=", mail.outbox[0].body)

    def test_connexion_ne_peut_pas_donner_un_jeton_a_un_administrateur(self):
        administrateur = Utilisateur.objects.create_superuser(
            username="admin@akasha.test",
            email="admin@akasha.test",
            password="MotDePasseAdmin2026!",
        )
        tentative_injection = self.client.post(
            "/api/comptes/connexion/",
            {"email": "admin@akasha.test' OR '1'='1", "password": "invalide"},
            format="json",
        )
        self.assertNotEqual(tentative_injection.status_code, status.HTTP_200_OK)
        self.assertNotIn("access", tentative_injection.data)

        connexion_admin = self.client.post(
            "/api/comptes/connexion/",
            {"email": administrateur.email, "password": "MotDePasseAdmin2026!"},
            format="json",
        )
        self.assertEqual(connexion_admin.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access", connexion_admin.data)

    def test_connexion_jwt(self):
        # Création de l'utilisateur
        user = Utilisateur.objects.create_user(
            username="marc.kouassi@akasha.ci",
            email="marc.kouassi@akasha.ci",
            password="MotDePasseSecurise2026!",
            first_name="Marc",
        )

        reponse = self.client.post(
            "/api/comptes/connexion/",
            {"email": "marc.kouassi@akasha.ci", "password": "MotDePasseSecurise2026!"},
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertIn("access", reponse.data)
        self.assertIn("refresh", reponse.data)

    def test_mise_a_jour_role_actif(self):
        user = Utilisateur.objects.create_user(
            username="fatou.diarra@akasha.ci",
            email="fatou.diarra@akasha.ci",
            password="MotDePasseSecurise2026!",
            first_name="Fatou",
            roles_professionnels=["professionnel", "client"],
            role_actif="professionnel",
        )
        self.client.force_authenticate(user=user)

        # Bascule vers le rôle client
        reponse = self.client.patch(
            "/api/comptes/moi/role-actif/",
            {"role_actif": "client"},
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["role_actif"], "client")

    def test_inscription_exige_les_conditions(self):
        donnees = {**self.donnees_inscription, "conditions_acceptees": False}
        reponse = self.client.post(
            "/api/comptes/inscription/",
            donnees,
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inscription_normalise_et_conserve_le_consentement(self):
        donnees = {
            **self.donnees_inscription,
            "email": "  Marc.Kouassi@Akasha.CI ",
        }
        reponse = self.client.post(
            "/api/comptes/inscription/",
            donnees,
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reponse.data["utilisateur"]["email"], "marc.kouassi@akasha.ci")
        self.assertIsNotNone(
            reponse.data["utilisateur"]["consentement_conditions_le"]
        )
        self.assertEqual(
            reponse.data["utilisateur"]["consentement_conditions_version"],
            "1.0",
        )

    def test_onboarding_refuse_les_roles_plateforme(self):
        user = Utilisateur.objects.create_user(
            username="nadia@akasha.ci",
            email="nadia@akasha.ci",
            password="test-password-for-account-tests",
        )
        self.client.force_authenticate(user=user)
        reponse = self.client.post(
            "/api/comptes/moi/onboarding/",
            {
                "roles_professionnels": ["professionnel", "administrateur"],
                "role_actif": "professionnel",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compte_modifie_identite_sans_modifier_email_roles_ou_verification(self):
        utilisateur = Utilisateur.objects.create_user(
            username="samira@example.test",
            email="samira@example.test",
            password="MotDePasseSecurise2026!",
            roles_professionnels=["professionnel", "client"],
            role_actif="client",
        )
        self.client.force_authenticate(user=utilisateur)

        reponse = self.client.patch(
            "/api/comptes/moi/",
            {
                "first_name": " Samira ",
                "last_name": "Koné",
                "telephone": "+225 07 12 34 56 78",
                "pays": "ci",
                "email": "autre@example.test",
                "roles_professionnels": ["administrateur"],
                "role_actif": "administrateur",
                "est_verifie": True,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        utilisateur.refresh_from_db()
        self.assertEqual(utilisateur.first_name, "Samira")
        self.assertEqual(utilisateur.last_name, "Koné")
        self.assertEqual(utilisateur.telephone, "+2250712345678")
        self.assertEqual(utilisateur.pays, "CI")
        self.assertEqual(utilisateur.email, "samira@example.test")
        self.assertEqual(utilisateur.roles_professionnels, ["professionnel", "client"])
        self.assertEqual(utilisateur.role_actif, "client")
        self.assertFalse(utilisateur.est_verifie)

    def test_compte_refuse_pays_et_telephone_invalides(self):
        utilisateur = Utilisateur.objects.create_user(
            username="awa@example.test",
            email="awa@example.test",
            password="MotDePasseSecurise2026!",
        )
        self.client.force_authenticate(user=utilisateur)

        reponse = self.client.patch(
            "/api/comptes/moi/",
            {"pays": "CIV", "telephone": "----"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pays", reponse.data["erreurs"])
        self.assertIn("telephone", reponse.data["erreurs"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_reinitialisation_mot_de_passe_invalide_les_jetons_rafraichissement(self):
        utilisateur = Utilisateur.objects.create_user(
            username="mariam@example.test",
            email="mariam@example.test",
            password="AncienMotDePasse2026!",
        )
        demande = self.client.post(
            "/api/comptes/mot-de-passe/oublie/",
            {"email": utilisateur.email},
            format="json",
        )
        self.assertEqual(demande.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(mail.outbox), 1)
        contenu = mail.outbox[0].body
        lien = next(ligne for ligne in contenu.splitlines() if ligne.startswith("akasha://"))
        parametres = dict(partie.split("=", 1) for partie in lien.split("?", 1)[1].split("&"))

        reinitialisation = self.client.post(
            "/api/comptes/mot-de-passe/reinitialiser/",
            {**parametres, "mot_de_passe": "NouveauMotDePasse2026!"},
            format="json",
        )
        self.assertEqual(reinitialisation.status_code, status.HTTP_204_NO_CONTENT)
        utilisateur.refresh_from_db()
        self.assertTrue(utilisateur.check_password("NouveauMotDePasse2026!"))
        connexion = self.client.post(
            "/api/comptes/connexion/",
            {"email": utilisateur.email, "password": "NouveauMotDePasse2026!"},
            format="json",
        )
        self.assertEqual(connexion.status_code, status.HTTP_200_OK)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_verification_email_confirme_le_compte(self):
        utilisateur = Utilisateur.objects.create_user(
            username="aicha@example.test",
            email="aicha@example.test",
            password="MotDePasseSecurise2026!",
        )
        self.client.force_authenticate(user=utilisateur)
        envoi = self.client.post(
            "/api/comptes/verification-email/envoyer/", {}, format="json"
        )
        self.assertEqual(envoi.status_code, status.HTTP_204_NO_CONTENT)
        lien = next(
            ligne
            for ligne in mail.outbox[0].body.splitlines()
            if ligne.startswith("akasha://")
        )
        jeton = lien.split("token=", 1)[1]

        confirmation = self.client.post(
            "/api/comptes/verification-email/confirmer/",
            {"token": jeton},
            format="json",
        )
        self.assertEqual(confirmation.status_code, status.HTTP_204_NO_CONTENT)
        utilisateur.refresh_from_db()
        self.assertTrue(utilisateur.est_verifie)
