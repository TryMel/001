from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from opportunites.models import Opportunite
from rest_framework import status
from rest_framework.test import APIClient
from PIL import Image

from internationalisation.models import EntrepriseReference, Marche
from .models import AppartenanceOrganisation, Organisation

Utilisateur = get_user_model()


class OrganisationsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.proprietaire = Utilisateur.objects.create_user(
            username="proprietaire@akasha.ci",
            email="proprietaire@akasha.ci",
            password="test-password-for-organization-tests",
        )
        self.membre = Utilisateur.objects.create_user(
            username="membre@akasha.ci",
            email="membre@akasha.ci",
            password="test-password-for-organization-tests",
        )
        self.autre = Utilisateur.objects.create_user(
            username="autre@akasha.ci",
            email="autre@akasha.ci",
            password="test-password-for-organization-tests",
        )

        self.proprietaire.role_actif = "organisation"
        self.proprietaire.roles_professionnels = ["organisation"]
        self.proprietaire.save(update_fields=("role_actif", "roles_professionnels"))

    def test_creation_organisation_et_proprietaire_sont_atomiques(self):
        self.client.force_authenticate(user=self.proprietaire)
        reponse = self.client.post(
            "/api/organisations/",
            {"nom": "Atelier Akasha", "pays": "CI"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        organisation = Organisation.objects.get(pk=reponse.data["id"])
        self.assertTrue(
            organisation.membres.filter(
                utilisateur=self.proprietaire,
                role=AppartenanceOrganisation.Role.PROPRIETAIRE,
            ).exists()
        )

    def test_creation_mobile_accepte_un_site_web_normalise_et_reference_absente(self):
        self.client.force_authenticate(user=self.proprietaire)

        reponse = self.client.post(
            "/api/organisations/",
            {
                "nom": "Atelier Akasha",
                "description": "",
                "pays": "CI",
                "ville": "",
                "site_web": "https://akasha.example",
                "reference_entreprise": None,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        organisation = Organisation.objects.get(pk=reponse.data["id"])
        self.assertEqual(organisation.site_web, "https://akasha.example")
        self.assertIsNone(organisation.reference_entreprise)

    def test_site_web_sans_protocole_est_refuse_par_l_api(self):
        self.client.force_authenticate(user=self.proprietaire)

        reponse = self.client.post(
            "/api/organisations/",
            {
                "nom": "Atelier Akasha",
                "pays": "CI",
                "site_web": "akasha.example",
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("site_web", reponse.data["erreurs"])
        self.assertFalse(Organisation.objects.filter(nom="Atelier Akasha").exists())

    def test_reference_entreprise_ne_valide_pas_automatiquement_une_organisation(self):
        marche = Marche.objects.get(code_pays="CI", est_actif=True)
        reference = EntrepriseReference.objects.create(
            marche=marche,
            nom="Entreprise déclarée",
        )
        self.client.force_authenticate(user=self.proprietaire)

        reponse = self.client.post(
            "/api/organisations/",
            {
                "nom": "Entreprise déclarée",
                "pays": "CI",
                "reference_entreprise": reference.pk,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        organisation = Organisation.objects.get(pk=reponse.data["id"])
        self.assertEqual(organisation.reference_entreprise, reference)
        self.assertFalse(organisation.est_verifiee)
        self.assertEqual(
            reponse.data["reference_entreprise_statut_verification"],
            "declaree",
        )

    def test_reference_entreprise_d_un_autre_pays_est_refusee(self):
        marche = Marche.objects.get(code_pays="CI", est_actif=True)
        reference = EntrepriseReference.objects.create(
            marche=marche,
            nom="Entreprise ivoirienne",
        )
        self.client.force_authenticate(user=self.proprietaire)

        reponse = self.client.post(
            "/api/organisations/",
            {
                "nom": "Entreprise",
                "pays": "FR",
                "reference_entreprise": reference.pk,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Organisation.objects.filter(nom="Entreprise").exists())

    def test_un_utilisateur_sans_role_organisation_ne_peut_pas_creer_une_organisation(self):
        self.client.force_authenticate(user=self.autre)

        reponse = self.client.post(
            "/api/organisations/",
            {"nom": "Organisation non autorisée", "pays": "CI"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Organisation.objects.filter(nom="Organisation non autorisée").exists()
        )

    def test_liste_et_detail_des_organisations_sont_limites_aux_membres(self):
        organisation_autorisee = Organisation.objects.create(nom="Mon organisation")
        AppartenanceOrganisation.objects.create(
            organisation=organisation_autorisee,
            utilisateur=self.proprietaire,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        organisation_privee = Organisation.objects.create(nom="Organisation privée")

        self.client.force_authenticate(user=self.proprietaire)
        liste = self.client.get("/api/organisations/")
        detail = self.client.get(f"/api/organisations/{organisation_privee.pk}/")

        self.assertEqual(liste.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [element["id"] for element in liste.data["results"]],
            [organisation_autorisee.pk],
        )
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_une_organisation_avec_des_offres_ne_peut_pas_etre_supprimee(self):
        organisation = Organisation.objects.create(nom="Organisation avec offre")
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.proprietaire,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        Opportunite.objects.create(
            createur=self.proprietaire,
            organisation=organisation,
            titre="Offre à conserver",
            description="L'organisation ne peut pas être supprimée.",
            type=Opportunite.Type.EMPLOI,
        )
        self.client.force_authenticate(user=self.proprietaire)

        reponse = self.client.delete(f"/api/organisations/{organisation.pk}/")

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Organisation.objects.filter(pk=organisation.pk).exists())

    def test_profil_public_organisation_verifie_et_photo(self):
        organisation = Organisation.objects.create(
            nom="Atelier Akasha",
            description="Services professionnels",
        )
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.proprietaire,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        self.client.force_authenticate(user=self.proprietaire)
        self.assertEqual(
            self.client.get(
                f"/api/organisations/publiques/{organisation.pk}/"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

        contenu = BytesIO()
        Image.new("RGB", (16, 16), color=(103, 58, 183)).save(
            contenu, format="PNG"
        )
        photo = SimpleUploadedFile(
            "logo.png",
            contenu.getvalue(),
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                modification = self.client.patch(
                    f"/api/organisations/{organisation.pk}/",
                    {"photo": photo},
                    format="multipart",
                )
                self.assertEqual(
                    modification.status_code, status.HTTP_200_OK, modification.data
                )

                organisation.est_verifiee = True
                organisation.save(update_fields=("est_verifiee",))
                self.client.force_authenticate(user=None)
                reponse = self.client.get(
                    f"/api/organisations/publiques/{organisation.pk}/"
                )
                self.assertEqual(reponse.status_code, status.HTTP_200_OK)
                self.assertEqual(reponse.data["nom"], "Atelier Akasha")
                self.assertTrue(reponse.data["photo_url"].endswith(".png"))
                self.assertNotIn("membres", reponse.data)

    def test_seul_le_proprietaire_peut_ajouter_un_membre(self):
        organisation = Organisation.objects.create(nom="Atelier Akasha")
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.proprietaire,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.membre,
            role=AppartenanceOrganisation.Role.RECRUTEUR,
        )
        self.client.force_authenticate(user=self.membre)

        reponse = self.client.post(
            "/api/organisations/membres/",
            {
                "organisation": organisation.pk,
                "utilisateur": self.autre.pk,
                "role": AppartenanceOrganisation.Role.MEMBRE,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            organisation.membres.filter(utilisateur=self.autre).exists()
        )

    def test_un_membre_ne_peut_pas_s_autoproclamer_proprietaire(self):
        organisation = Organisation.objects.create(nom="Atelier Akasha")
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.proprietaire,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        self.client.force_authenticate(user=self.proprietaire)

        reponse = self.client.post(
            "/api/organisations/membres/",
            {
                "organisation": organisation.pk,
                "utilisateur": self.membre.pk,
                "role": AppartenanceOrganisation.Role.PROPRIETAIRE,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            organisation.membres.filter(
                role=AppartenanceOrganisation.Role.PROPRIETAIRE
            ).count(),
            1,
        )

    def test_un_membre_ne_consulte_pas_les_autres_membres_de_l_organisation(self):
        organisation = Organisation.objects.create(nom="Atelier Akasha")
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.proprietaire,
            role=AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=self.membre,
            role=AppartenanceOrganisation.Role.GESTIONNAIRE,
        )
        self.client.force_authenticate(user=self.membre)

        reponse = self.client.get("/api/organisations/membres/")

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reponse.data["results"]), 1)
        self.assertEqual(
            reponse.data["results"][0]["utilisateur"],
            self.membre.pk,
        )
