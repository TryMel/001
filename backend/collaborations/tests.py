from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from PIL import Image

from organisations.models import AppartenanceOrganisation, Organisation
from profils.models import ProfilProfessionnel

from .models import Collaboration, DemandeService, OffreService, Proposition

Utilisateur = get_user_model()


class CollaborationsTests(TestCase):
    def setUp(self):
        self.media_temp = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_temp.name)
        self.media_override.enable()
        self.client_api = APIClient()
        self.client_user = Utilisateur.objects.create_user(
            username="client@akasha.ci",
            email="client@akasha.ci",
            password="local-test-password",
            first_name="Jean",
            role_actif="client",
            roles_professionnels=["client"],
        )
        self.pro_user = Utilisateur.objects.create_user(
            username="artisan@akasha.ci",
            email="artisan@akasha.ci",
            password="local-test-password",
            first_name="Koffi",
            role_actif="professionnel",
            roles_professionnels=["professionnel"],
            onboarding_termine=True,
        )
        ProfilProfessionnel.objects.create(
            utilisateur=self.pro_user,
            titre="Plombier",
            visible_publiquement=True,
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_temp.cleanup()

    @staticmethod
    def image_telechargee(nom):
        contenu = BytesIO()
        Image.new("RGB", (16, 16), color=(103, 58, 183)).save(contenu, format="PNG")
        return SimpleUploadedFile(nom, contenu.getvalue(), content_type="image/png")

    def ajouter_photo(self, objet, nom="photo.png"):
        objet.photo.save(nom, self.image_telechargee(nom), save=False)
        objet.save(update_fields=("photo",))

    def creer_demande_publiee(self):
        self.client_api.force_authenticate(user=self.client_user)
        reponse = self.client_api.post(
            "/api/collaborations/demandes/",
            {
                "titre": "Rénovation plomberie",
                "description": "Remplacement de tuyauterie et installation.",
                "ville": "Abidjan",
                "budget_maximum": 85000,
                "devise": "XOF",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(reponse.data["statut"], DemandeService.Statut.BROUILLON)
        demande_id = reponse.data["id"]
        self.ajouter_photo(DemandeService.objects.get(pk=demande_id), "demande.png")
        publication = self.client_api.post(
            f"/api/collaborations/demandes/{demande_id}/publier/",
            {},
            format="json",
        )
        self.assertEqual(publication.status_code, status.HTTP_200_OK, publication.data)
        return demande_id

    def test_demande_publiee_et_proposition_creent_une_collaboration(self):
        demande_id = self.creer_demande_publiee()
        self.client_api.force_authenticate(user=self.pro_user)

        reponse_proposition = self.client_api.post(
            f"/api/collaborations/demandes/{demande_id}/propositions/",
            {
                "montant": 80000,
                "devise": "XOF",
                "delai_jours": 3,
                "message": "Je peux commencer demain.",
            },
            format="json",
        )
        self.assertEqual(
            reponse_proposition.status_code,
            status.HTTP_201_CREATED,
            reponse_proposition.data,
        )
        proposition_id = reponse_proposition.data["id"]

        doublon = self.client_api.post(
            f"/api/collaborations/demandes/{demande_id}/propositions/",
            {
                "montant": 79000,
                "devise": "XOF",
                "delai_jours": 2,
                "message": "Une autre proposition.",
            },
            format="json",
        )
        self.assertEqual(doublon.status_code, status.HTTP_409_CONFLICT)

        self.client_api.force_authenticate(user=self.client_user)
        reponse_acceptation = self.client_api.post(
            f"/api/collaborations/propositions/{proposition_id}/accepter/",
            {},
            format="json",
        )
        self.assertEqual(
            reponse_acceptation.status_code,
            status.HTTP_201_CREATED,
            reponse_acceptation.data,
        )
        self.assertEqual(
            reponse_acceptation.data["statut"],
            Collaboration.Statut.ACCORDEE,
        )
        demande = DemandeService.objects.get(pk=demande_id)
        self.assertEqual(demande.statut, DemandeService.Statut.ATTRIBUEE)
        self.assertEqual(Collaboration.objects.count(), 1)

    def test_seuls_les_professionnels_actifs_voient_les_demandes_publiques(self):
        demande_id = self.creer_demande_publiee()
        autre = Utilisateur.objects.create_user(
            username="autre@akasha.ci",
            email="autre@akasha.ci",
            password="local-test-password",
        )
        self.client_api.force_authenticate(user=autre)
        reponse = self.client_api.get(
            f"/api/collaborations/demandes/{demande_id}/"
        )
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)

    def test_acceptation_mutuelle_requise_pour_terminer_une_collaboration(self):
        demande_id = self.creer_demande_publiee()
        self.client_api.force_authenticate(user=self.pro_user)
        proposition = self.client_api.post(
            f"/api/collaborations/demandes/{demande_id}/propositions/",
            {
                "montant": 80000,
                "devise": "XOF",
                "delai_jours": 3,
                "message": "Je peux commencer demain.",
            },
            format="json",
        ).data
        self.client_api.force_authenticate(user=self.client_user)
        collaboration = self.client_api.post(
            f"/api/collaborations/propositions/{proposition['id']}/accepter/",
            {},
            format="json",
        ).data
        self.client_api.post(
            f"/api/collaborations/collaborations/{collaboration['id']}/demarrer/",
            {},
        )
        fin_client = self.client_api.post(
            f"/api/collaborations/collaborations/{collaboration['id']}/confirmer-terminaison/",
            {},
        )
        self.assertEqual(fin_client.data["statut"], Collaboration.Statut.EN_COURS)
        self.assertTrue(fin_client.data["client_a_confirme_fin"])
        self.assertFalse(fin_client.data["prestataire_a_confirme_fin"])

        self.client_api.force_authenticate(user=self.pro_user)
        fin_prestataire = self.client_api.post(
            f"/api/collaborations/collaborations/{collaboration['id']}/confirmer-terminaison/",
            {},
        )
        self.assertEqual(
            fin_prestataire.data["statut"],
            Collaboration.Statut.TERMINEE,
        )
        self.assertIsNotNone(fin_prestataire.data["terminee_le"])

    def test_publication_organisation_exige_permission_et_verification(self):
        organisation = Organisation.objects.create(
            nom="Atelier vérifié",
            est_verifiee=False,
        )
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.client_user,
            role=AppartenanceOrganisation.Role.GESTIONNAIRE,
        )
        self.client_api.force_authenticate(user=self.client_user)
        reponse = self.client_api.post(
            "/api/collaborations/demandes/",
            {
                "organisation": organisation.pk,
                "titre": "Réparer le local",
                "description": "Travaux de plomberie.",
                "devise": "XOF",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        publication = self.client_api.post(
            f"/api/collaborations/demandes/{reponse.data['id']}/publier/",
            {},
        )
        self.assertEqual(publication.status_code, status.HTTP_400_BAD_REQUEST)
        organisation.est_verifiee = True
        organisation.save(update_fields=("est_verifiee",))
        self.ajouter_photo(DemandeService.objects.get(pk=reponse.data["id"]), "demande-organisation.png")
        publication = self.client_api.post(
            f"/api/collaborations/demandes/{reponse.data['id']}/publier/",
            {},
        )
        self.assertEqual(publication.status_code, status.HTTP_200_OK)

    def test_gestionnaire_organisation_accepte_et_suit_la_collaboration(self):
        organisation = Organisation.objects.create(
            nom="Atelier vérifié",
            est_verifiee=True,
        )
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.client_user,
            role=AppartenanceOrganisation.Role.GESTIONNAIRE,
        )
        self.client_api.force_authenticate(user=self.client_user)
        demande = self.client_api.post(
            "/api/collaborations/demandes/",
            {
                "organisation": organisation.pk,
                "titre": "Réparer le local",
                "description": "Travaux de plomberie.",
                "devise": "XOF",
            },
            format="json",
        ).data
        self.ajouter_photo(DemandeService.objects.get(pk=demande["id"]), "demande-gestionnaire.png")
        self.client_api.post(
            f"/api/collaborations/demandes/{demande['id']}/publier/",
            {},
        )
        self.client_api.force_authenticate(user=self.pro_user)
        proposition = self.client_api.post(
            f"/api/collaborations/demandes/{demande['id']}/propositions/",
            {
                "montant": 80000,
                "devise": "XOF",
                "delai_jours": 3,
                "message": "Je peux commencer demain.",
            },
            format="json",
        ).data
        self.client_api.force_authenticate(user=self.client_user)
        reponse = self.client_api.post(
            f"/api/collaborations/propositions/{proposition['id']}/accepter/",
            {},
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        liste = self.client_api.get("/api/collaborations/collaborations/")
        self.assertEqual(liste.status_code, status.HTTP_200_OK)
        self.assertEqual(liste.data["results"][0]["id"], reponse.data["id"])

    def test_service_est_public_uniquement_apres_publication_et_profil_visible(self):
        self.client_api.force_authenticate(user=self.pro_user)
        reponse = self.client_api.post(
            "/api/collaborations/services/",
            {
                "titre": "Installation sanitaire",
                "description": "Installation et réparation de plomberie.",
                "tarification": "forfait",
                "prix": 25000,
                "devise": "XOF",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        offre_id = reponse.data["id"]
        self.client_api.force_authenticate(user=None)
        self.assertEqual(
            self.client_api.get(f"/api/collaborations/services/{offre_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.client_api.force_authenticate(user=self.pro_user)
        self.ajouter_photo(OffreService.objects.get(pk=offre_id), "service.png")
        publication = self.client_api.post(
            f"/api/collaborations/services/{offre_id}/publier/",
            {},
        )
        self.assertEqual(publication.status_code, status.HTTP_200_OK)
        self.client_api.force_authenticate(user=None)
        self.assertEqual(
            self.client_api.get(f"/api/collaborations/services/{offre_id}/").status_code,
            status.HTTP_200_OK,
        )

    def test_brouillon_de_service_refuse_un_prix_incoherent(self):
        self.client_api.force_authenticate(user=self.pro_user)
        reponse = self.client_api.post(
            "/api/collaborations/services/",
            {
                "titre": "Service incohérent",
                "description": "Description.",
                "tarification": "forfait",
                "devise": "XOF",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(OffreService.objects.exists())

    def test_photos_service_et_demande_sont_accessibles_sur_les_listes_publiques(self):
        def image_telechargee(nom):
            contenu = BytesIO()
            Image.new("RGB", (16, 16), color=(103, 58, 183)).save(
                contenu, format="PNG"
            )
            return SimpleUploadedFile(
                nom,
                contenu.getvalue(),
                content_type="image/png",
            )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client_api.force_authenticate(user=self.pro_user)
                service = self.client_api.post(
                    "/api/collaborations/services/",
                    {
                        "titre": "Installation sanitaire",
                        "description": "Pose et réparation de plomberie.",
                        "tarification": "sur_devis",
                        "devise": "XOF",
                        "photo": image_telechargee("service.png"),
                    },
                    format="multipart",
                )
                self.assertEqual(
                    service.status_code, status.HTTP_201_CREATED, service.data
                )
                self.assertTrue(service.data["photo_url"].endswith(".png"))
                self.assertIsNone(service.data["prestataire_photo_url"])
                self.client_api.post(
                    f"/api/collaborations/services/{service.data['id']}/publier/",
                    {},
                )
                self.client_api.force_authenticate(user=None)
                service_public = self.client_api.get(
                    f"/api/collaborations/services/{service.data['id']}/"
                )
                self.assertEqual(service_public.status_code, status.HTTP_200_OK)
                self.assertEqual(
                    service_public.data["photo_url"], service.data["photo_url"]
                )

                self.client_api.force_authenticate(user=self.client_user)
                demande = self.client_api.post(
                    "/api/collaborations/demandes/",
                    {
                        "titre": "Rénover une salle de bain",
                        "description": "Remplacer les équipements sanitaires.",
                        "devise": "XOF",
                        "visibilite": "publique",
                        "photo": image_telechargee("besoin.png"),
                    },
                    format="multipart",
                )
                self.assertEqual(
                    demande.status_code, status.HTTP_201_CREATED, demande.data
                )
                self.assertTrue(demande.data["photo_url"].endswith(".png"))
