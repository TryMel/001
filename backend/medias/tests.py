from io import BytesIO
from pathlib import Path
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from configuration.medias import compresser_image
from profils.models import ProfilProfessionnel

from .models import ImageContenu


Utilisateur = get_user_model()


def creer_image_png(nom="image.png", taille=(2400, 1200)):
    contenu = BytesIO()
    Image.new("RGB", taille, color=(110, 80, 190)).save(contenu, format="PNG")
    return SimpleUploadedFile(nom, contenu.getvalue(), content_type="image/png")


class CompressionImageTests(TestCase):
    def test_compresser_redimensionne_et_conserve_le_format(self):
        image_televersee = serializers.ImageField().run_validation(creer_image_png())
        image_compressee = compresser_image(image_televersee)

        with Image.open(image_compressee) as image:
            self.assertEqual(image.format, "PNG")
            self.assertLessEqual(max(image.size), 1600)
        self.assertTrue(image_compressee.name.endswith(".png"))

    def test_refuser_un_fichier_superieur_a_cinq_mo(self):
        image = SimpleUploadedFile(
            "trop-lourde.png",
            b"x" * (5 * 1024 * 1024 + 1),
            content_type="image/png",
        )

        with self.assertRaisesMessage(ValidationError, "ne doit pas dépasser 5 Mo"):
            compresser_image(image)


class GalerieImagesApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        utilisateur = Utilisateur.objects.create_user(
            username="recruteur@akasha.test",
            email="recruteur@akasha.test",
            password="mot-de-passe-test",
            role_actif="recruteur",
            roles_professionnels=["recruteur"],
        )
        self.client.force_authenticate(utilisateur)

    def test_creer_une_opportunite_avec_deux_images_compressees(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                reponse = self.client.post(
                    "/api/opportunites/",
                    {
                        "titre": "Projet de démonstration",
                        "description": "Un contenu qui présente le projet.",
                        "type": "mission",
                        "images": [
                            creer_image_png("premiere.png"),
                            creer_image_png("seconde.png"),
                        ],
                    },
                    format="multipart",
                )

                self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
                self.assertEqual(len(reponse.data["images_url"]), 2)
                self.assertEqual(ImageContenu.objects.count(), 2)
                anciens_fichiers = [
                    Path(image.fichier.path) for image in ImageContenu.objects.all()
                ]
                for image in ImageContenu.objects.all():
                    with Image.open(image.fichier.path) as contenu:
                        self.assertLessEqual(max(contenu.size), 1600)

                mise_a_jour = self.client.patch(
                    f"/api/opportunites/{reponse.data['id']}/",
                    {"images": [creer_image_png("remplacement.png")]},
                    format="multipart",
                )

                self.assertEqual(
                    mise_a_jour.status_code,
                    status.HTTP_200_OK,
                    mise_a_jour.data,
                )
                self.assertEqual(len(mise_a_jour.data["images_url"]), 1)
                self.assertEqual(ImageContenu.objects.count(), 1)
                self.assertTrue(all(not chemin.exists() for chemin in anciens_fichiers))

    def test_refuser_plus_de_cinq_images(self):
        reponse = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Projet de démonstration",
                "description": "Un contenu qui présente le projet.",
                "type": "mission",
                "images": [creer_image_png(f"{position}.png") for position in range(6)],
            },
            format="multipart",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", reponse.data["erreurs"])
        self.assertEqual(ImageContenu.objects.count(), 0)

    def test_la_photo_principale_compte_dans_la_limite_de_cinq_images(self):
        professionnel = Utilisateur.objects.create_user(
            username="prestataire-images@akasha.test",
            email="prestataire-images@akasha.test",
            password="mot-de-passe-test",
            role_actif="professionnel",
            roles_professionnels=["professionnel"],
        )
        ProfilProfessionnel.objects.create(
            utilisateur=professionnel,
            visible_publiquement=True,
        )
        self.client.force_authenticate(professionnel)
        reponse = self.client.post(
            "/api/collaborations/services/",
            {
                "titre": "Installation électrique",
                "description": "Installation et rénovation.",
                "photo": creer_image_png("photo-principale.png"),
                "images": [
                    creer_image_png(f"image-{position}.png")
                    for position in range(5)
                ],
            },
            format="multipart",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", reponse.data["erreurs"])
        self.assertEqual(ImageContenu.objects.count(), 0)

    def test_creer_un_service_avec_une_galerie(self):
        professionnel = Utilisateur.objects.create_user(
            username="prestataire@akasha.test",
            email="prestataire@akasha.test",
            password="mot-de-passe-test",
            role_actif="professionnel",
            roles_professionnels=["professionnel"],
        )
        ProfilProfessionnel.objects.create(
            utilisateur=professionnel,
            visible_publiquement=True,
        )
        self.client.force_authenticate(professionnel)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                reponse = self.client.post(
                    "/api/collaborations/services/",
                    {
                        "titre": "Installation électrique",
                        "description": "Installation et rénovation.",
                        "ville": "Abidjan",
                        "images": [
                            creer_image_png("service-1.png"),
                            creer_image_png("service-2.png"),
                        ],
                    },
                    format="multipart",
                )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(len(reponse.data["images_url"]), 2)

    def test_creer_une_demande_avec_une_galerie(self):
        client = Utilisateur.objects.create_user(
            username="client@akasha.test",
            email="client@akasha.test",
            password="mot-de-passe-test",
            role_actif="client",
            roles_professionnels=["client"],
        )
        self.client.force_authenticate(client)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                reponse = self.client.post(
                    "/api/collaborations/demandes/",
                    {
                        "titre": "Rénovation d’un local",
                        "description": "Recherche d’un artisan qualifié.",
                        "ville": "Abidjan",
                        "images": [creer_image_png("besoin.png")],
                    },
                    format="multipart",
                )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(len(reponse.data["images_url"]), 1)

    def test_creer_une_realisation_de_portfolio_avec_une_galerie(self):
        professionnel = Utilisateur.objects.create_user(
            username="portfolio@akasha.test",
            email="portfolio@akasha.test",
            password="mot-de-passe-test",
            role_actif="professionnel",
            roles_professionnels=["professionnel"],
        )
        self.client.force_authenticate(professionnel)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                reponse = self.client.post(
                    "/api/portfolios/realisations/",
                    {
                        "titre": "Rénovation d’un atelier",
                        "description": "Projet réalisé à Abidjan.",
                        "images": [creer_image_png("realisation.png")],
                    },
                    format="multipart",
                )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(len(reponse.data["images_url"]), 1)
