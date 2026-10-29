from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from PIL import Image

from portfolios.models import Experience, Qualification, Realisation
from referentiel.models import Competence, Metier
from .models import (
    CreneauHebdomadaire,
    DisponibiliteProfil,
    NiveauCompetence,
    ProfilProfessionnel,
)


Utilisateur = get_user_model()


class ProfilActuelTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.utilisateur = Utilisateur.objects.create_user(
            username="lea@example.test",
            email="lea@example.test",
            password="MotDePasseSecurise2026!",
            first_name="Léa",
            last_name="Traoré",
            roles_professionnels=["professionnel", "client"],
            role_actif="client",
        )
        self.client.force_authenticate(self.utilisateur)
        self.metier = Metier.objects.create(code="dev-web", nom="Développement web")
        self.competence = Competence.objects.create(nom="Python")

    def test_lecture_cree_le_profil_et_ne_retourne_que_des_donnees_professionnelles(self):
        reponse = self.client.get("/api/profils/moi/")

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertTrue(ProfilProfessionnel.objects.filter(utilisateur=self.utilisateur).exists())
        self.assertEqual(reponse.data["titre"], "")
        for champ_prive in (
            "email",
            "telephone",
            "est_verifie",
            "roles_professionnels",
            "utilisateur",
        ):
            self.assertNotIn(champ_prive, reponse.data)
        self.assertEqual(
            self.client.get("/api/profils/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_modification_partielle_metier_et_competences(self):
        self.client.get("/api/profils/moi/")
        reponse = self.client.patch(
            "/api/profils/moi/",
            {
                "titre": "Développeuse",
                "ville": "Abidjan",
                "metier": self.metier.pk,
                "competences": [
                    {
                        "competence": self.competence.pk,
                        "niveau": "expert",
                        "preuve": "https://example.test/preuve",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.data)
        self.assertEqual(reponse.data["metier_nom"], "Développement web")
        self.assertEqual(reponse.data["competences_detail"][0]["niveau"], "expert")
        profil = ProfilProfessionnel.objects.get(utilisateur=self.utilisateur)
        self.assertEqual(profil.ville, "Abidjan")
        self.assertEqual(profil.niveaucompetence_set.count(), 1)

    def test_competences_invalides_ne_modifient_pas_le_profil(self):
        profil = ProfilProfessionnel.objects.create(
            utilisateur=self.utilisateur, titre="Titre existant"
        )
        NiveauCompetence.objects.create(
            profil=profil, competence=self.competence, niveau="autonome"
        )
        reponse = self.client.patch(
            "/api/profils/moi/",
            {
                "titre": "Titre changé",
                "competences": [
                    {"competence": self.competence.pk},
                    {"competence": self.competence.pk},
                ],
            },
            format="json",
        )

        profil.refresh_from_db()
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(profil.titre, "Titre existant")
        self.assertEqual(profil.niveaucompetence_set.count(), 1)

    def test_competence_personnalisee_reste_propre_au_profil(self):
        reponse = self.client.patch(
            "/api/profils/moi/",
            {
                "metier": self.metier.pk,
                "competences": [
                    {
                        "competence_personnalisee": "Gestion d’un atelier",
                        "niveau": "autonome",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.data)
        self.assertEqual(
            reponse.data["competences_detail"][0]["competence_nom"],
            "Gestion d’un atelier",
        )
        self.assertTrue(reponse.data["competences_detail"][0]["est_personnalisee"])
        self.assertIsNone(reponse.data["competences_detail"][0]["competence"])
        self.assertEqual(Competence.objects.count(), 1)

    def test_competence_mappée_a_un_autre_metier_est_refusee(self):
        autre_metier = Metier.objects.create(code="plomberie", nom="Plomberie")
        self.competence.metiers.add(autre_metier)

        reponse = self.client.patch(
            "/api/profils/moi/",
            {
                "metier": self.metier.pk,
                "competences": [{"competence": self.competence.pk}],
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        profil = ProfilProfessionnel.objects.get(utilisateur=self.utilisateur)
        self.assertIsNone(profil.metier)
        self.assertFalse(profil.niveaucompetence_set.exists())

    def test_roles_professionnels_additifs_autorisent_le_profil(self):
        self.assertEqual(
            self.client.get("/api/profils/moi/").status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(ProfilProfessionnel.objects.filter(utilisateur=self.utilisateur).exists())

    def test_role_non_professionnel_refuse_le_profil_sans_le_creer(self):
        utilisateur = Utilisateur.objects.create_user(
            username="client@example.test",
            email="client@example.test",
            password="MotDePasseSecurise2026!",
            roles_professionnels=["client"],
            role_actif="client",
        )
        self.client.force_authenticate(utilisateur)

        reponse = self.client.get("/api/profils/moi/")

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ProfilProfessionnel.objects.filter(utilisateur=utilisateur).exists())

    def test_lecture_du_profil_personnel_exige_authentification(self):
        self.client.force_authenticate(user=None)
        reponse = self.client.get("/api/profils/moi/")

        self.assertEqual(reponse.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profil_public_reste_ferme_jusqua_accord_explicite(self):
        profil = ProfilProfessionnel.objects.create(
            utilisateur=self.utilisateur,
            titre="Développeuse",
        )
        self.utilisateur.onboarding_termine = True
        self.utilisateur.save(update_fields=("onboarding_termine",))
        self.client.force_authenticate(user=None)

        reponse = self.client.get(f"/api/profils/{profil.pk}/")

        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)

    def test_profil_public_limite_les_champs_et_suit_le_consentement(self):
        profil = ProfilProfessionnel.objects.create(
            utilisateur=self.utilisateur,
            titre="Développeuse",
            biographie="Présentation publique",
            ville="Abidjan",
            visible_publiquement=True,
        )
        self.utilisateur.onboarding_termine = True
        self.utilisateur.save(update_fields=("onboarding_termine",))
        Experience.objects.create(
            profil=profil,
            organisation="Atelier",
            poste="Développeuse",
            description="Application web",
            debut="2022-01-01",
            est_attestee=True,
        )
        Qualification.objects.create(
            profil=profil,
            nom="Certification",
            organisme="Centre",
            reference="REFERENCE-PRIVEE",
            est_confirmee=True,
        )
        realisation = Realisation.objects.create(
            profil=profil,
            titre="Projet public",
            description="Une réalisation présentée publiquement.",
        )
        self.client.force_authenticate(user=None)

        reponse = self.client.get(f"/api/profils/{profil.pk}/")

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["nom"], "Léa Traoré")
        self.assertEqual(reponse.data["experiences"][0]["poste"], "Développeuse")
        self.assertTrue(reponse.data["experiences"][0]["est_attestee"])
        self.assertNotIn("email", reponse.data)
        self.assertNotIn("telephone", reponse.data)
        self.assertNotIn("reference", reponse.data["qualifications"][0])
        self.assertTrue(reponse.data["qualifications"][0]["est_confirmee"])
        self.assertEqual(reponse.data["realisations"][0]["titre"], realisation.titre)
        self.assertEqual(reponse.data["realisations"][0]["images_url"], [])
        self.assertNotIn("reference", reponse.data["realisations"][0])

        profil.visible_publiquement = False
        profil.save(update_fields=("visible_publiquement",))
        self.assertEqual(
            self.client.get(f"/api/profils/{profil.pk}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_photo_de_profil_n_est_exposee_qu_apres_activation_du_profil_public(self):
        profil = ProfilProfessionnel.objects.create(
            utilisateur=self.utilisateur,
            titre="Développeuse",
        )
        self.utilisateur.onboarding_termine = True
        self.utilisateur.save(update_fields=("onboarding_termine",))
        contenu = BytesIO()
        Image.new("RGB", (16, 16), color=(103, 58, 183)).save(contenu, format="PNG")
        contenu.seek(0)
        photo = SimpleUploadedFile(
            "portrait.png",
            contenu.read(),
            content_type="image/png",
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                reponse = self.client.patch(
                    "/api/profils/moi/",
                    {"photo": photo},
                    format="multipart",
                )
                self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.data)
                self.assertTrue(reponse.data["photo_url"].endswith(".png"))

                self.client.force_authenticate(user=None)
                self.assertEqual(
                    self.client.get(f"/api/profils/{profil.pk}/").status_code,
                    status.HTTP_404_NOT_FOUND,
                )

                profil.visible_publiquement = True
                profil.save(update_fields=("visible_publiquement",))
                public = self.client.get(f"/api/profils/{profil.pk}/")
                self.assertEqual(public.status_code, status.HTTP_200_OK)
                self.assertEqual(public.data["photo_url"], reponse.data["photo_url"])
                self.assertNotIn("email", public.data)


class DisponibilitesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.utilisateur = Utilisateur.objects.create_user(
            username="pro-dispo@example.test",
            email="pro-dispo@example.test",
            password="local-test-password",
            roles_professionnels=["professionnel"],
            role_actif="professionnel",
            onboarding_termine=True,
        )
        self.profil = ProfilProfessionnel.objects.create(
            utilisateur=self.utilisateur,
            visible_publiquement=True,
        )
        self.client.force_authenticate(user=self.utilisateur)

    def test_remplacement_des_creneaux_et_exceptions(self):
        reponse = self.client.put(
            "/api/profils/moi/disponibilites/",
            {
                "fuseau": "Africa/Abidjan",
                "creneaux": [
                    {"jour": 0, "debut": "09:00:00", "fin": "12:00:00"},
                    {"jour": 0, "debut": "13:00:00", "fin": "17:00:00"},
                ],
                "exceptions": [
                    {
                        "date": "2026-12-25",
                        "est_disponible": False,
                        "debut": None,
                        "fin": None,
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.data)
        self.assertEqual(len(reponse.data["creneaux"]), 2)
        self.assertEqual(len(reponse.data["exceptions"]), 1)

        public = self.client.get(
            f"/api/profils/{self.profil.pk}/disponibilites/"
        )
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        self.assertEqual(len(public.data["creneaux"]), 2)

    def test_chevauchements_fuseau_inconnu_et_exceptions_invalides_sont_refuses(self):
        base = {
            "fuseau": "Africa/Abidjan",
            "creneaux": [
                {"jour": 1, "debut": "09:00:00", "fin": "12:00:00"},
                {"jour": 1, "debut": "11:00:00", "fin": "13:00:00"},
            ],
            "exceptions": [],
        }
        reponse = self.client.put(
            "/api/profils/moi/disponibilites/",
            base,
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CreneauHebdomadaire.objects.exists())

        reponse = self.client.put(
            "/api/profils/moi/disponibilites/",
            {
                "fuseau": "Pays/Invalid",
                "creneaux": [],
                "exceptions": [],
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

        reponse = self.client.put(
            "/api/profils/moi/disponibilites/",
            {
                "fuseau": "Africa/Abidjan",
                "creneaux": [],
                "exceptions": [
                    {
                        "date": "2026-12-25",
                        "est_disponible": True,
                        "debut": "15:00:00",
                        "fin": "12:00:00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_availability_requires_explicit_profile_visibility(self):
        self.profil.visible_publiquement = False
        self.profil.save(update_fields=("visible_publiquement",))
        self.client.force_authenticate(user=None)

        reponse = self.client.get(
            f"/api/profils/{self.profil.pk}/disponibilites/"
        )
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)
