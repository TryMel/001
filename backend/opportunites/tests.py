from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from medias.models import ImageContenu
from organisations.models import AppartenanceOrganisation, Organisation
from opportunites.models import Candidature, HistoriqueCandidature, Opportunite
from notifications.models import Notification
from profils.models import ProfilProfessionnel
from referentiel.models import Competence, Metier

Utilisateur = get_user_model()


class OpportunitesTests(TestCase):
    def setUp(self):
        self.media_temp = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_temp.name)
        self.media_override.enable()
        self.client = APIClient()
        self.recruteur = Utilisateur.objects.create_user(
            username="recruteur@btp-ivoire.ci",
            email="recruteur@btp-ivoire.ci",
            password="MotDePasse2026!",
            first_name="Amadou",
            role_actif="recruteur",
        )
        self.candidat = Utilisateur.objects.create_user(
            username="candidat@akasha.ci",
            email="candidat@akasha.ci",
            password="MotDePasse2026!",
            first_name="Yao",
            role_actif="candidat",
        )

        self.recruteur.roles_professionnels = ["recruteur"]
        self.recruteur.save(update_fields=("roles_professionnels",))
        self.candidat.roles_professionnels = ["candidat"]
        self.candidat.save(update_fields=("roles_professionnels",))

    def tearDown(self):
        self.media_override.disable()
        self.media_temp.cleanup()

    def ajouter_image_opportunite(self, opportunite_id):
        contenu = BytesIO()
        Image.new("RGB", (16, 16), color=(42, 135, 118)).save(contenu, format="PNG")
        ImageContenu.objects.create(
            contenu=Opportunite.objects.get(pk=opportunite_id),
            fichier=SimpleUploadedFile("opportunite.png", contenu.getvalue(), content_type="image/png"),
            position=0,
        )

    def creer_organisation(self, nom, est_verifiee=True):
        organisation = Organisation.objects.create(
            nom=nom,
            est_verifiee=est_verifiee,
        )
        return organisation

    def ajouter_membre_organisation(self, organisation, utilisateur, role):
        return AppartenanceOrganisation.objects.create(
            organisation=organisation,
            utilisateur=utilisateur,
            role=role,
        )

    def test_creation_opportunite_et_candidature(self):
        # 1. Le recruteur publie une opportunité
        self.client.force_authenticate(user=self.recruteur)
        reponse_opp = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Chef de chantier BTP",
                "description": "Superviser les chantiers de construction à Cocody.",
                "type": "emploi",
                "ville": "Abidjan",
                "budget_minimum": 500000,
                "budget_maximum": 700000,
                "devise": "XOF",
            },
            format="json",
        )
        self.assertEqual(reponse_opp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reponse_opp.data["statut"], "brouillon")
        opportunite_id = reponse_opp.data["id"]
        self.ajouter_image_opportunite(opportunite_id)
        publication = self.client.post(
            f"/api/opportunites/{opportunite_id}/publier/",
            {},
            format="json",
        )
        self.assertEqual(publication.status_code, status.HTTP_200_OK)
        self.assertEqual(publication.data["statut"], "publiee")

        # 2. Le candidat postule à l'opportunité
        profil = ProfilProfessionnel.objects.create(
            utilisateur=self.candidat,
            titre="Chef de chantier",
            visible_publiquement=False,
        )
        self.client.force_authenticate(user=self.candidat)
        reponse_cand = self.client.post(
            "/api/opportunites/candidatures/",
            {
                "opportunite": opportunite_id,
                "message": "Bonjour, je suis disponible immédiatement avec 4 ans d'expérience en génie civil.",
                "consentement_partage_profil": True,
            },
            format="json",
        )
        self.assertEqual(reponse_cand.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reponse_cand.data["statut"], "envoyee")
        candidature_id = reponse_cand.data["id"]
        self.assertTrue(
            Notification.objects.filter(
                utilisateur=self.recruteur,
                titre="Nouvelle candidature",
            ).exists()
        )
        self.assertIsNotNone(Candidature.objects.get(pk=candidature_id).partage_profil_consenti_le)
        profil.titre = "Profil modifié après la candidature"
        profil.save(update_fields=("titre",))
        candidature_du_candidat = self.client.get(
            f"/api/opportunites/candidatures/{candidature_id}/"
        )
        self.assertEqual(candidature_du_candidat.status_code, status.HTTP_200_OK)
        self.assertIsNone(candidature_du_candidat.data["profil_partage"])

        reponse_cand_duplicate = self.client.post(
            "/api/opportunites/candidatures/",
            {
                "opportunite": opportunite_id,
                "message": "Nouvelle tentative.",
                "consentement_partage_profil": True,
            },
            format="json",
        )
        self.assertEqual(reponse_cand_duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.recruteur)
        recues = self.client.get("/api/opportunites/candidatures/recues/")
        self.assertEqual(recues.status_code, status.HTTP_200_OK)
        self.assertEqual(len(recues.data["results"]), 1)
        profil_partage = recues.data["results"][0]["profil_partage"]
        self.assertEqual(profil_partage["titre"], "Chef de chantier")
        self.assertNotIn("email", profil_partage)
        self.assertEqual(profil_partage["titre"], "Chef de chantier")

        transition = self.client.post(
            f"/api/opportunites/candidatures/{candidature_id}/transition/",
            {"statut": "en_cours", "expected_version": 1},
            format="json",
        )
        self.assertEqual(transition.status_code, status.HTTP_200_OK)
        self.assertEqual(transition.data["statut"], "en_cours")
        self.assertEqual(transition.data["version"], 2)
        self.assertEqual(
            HistoriqueCandidature.objects.filter(
                candidature_id=candidature_id,
            ).count(),
            2,
        )

        conflit = self.client.post(
            f"/api/opportunites/candidatures/{candidature_id}/transition/",
            {"statut": "retenue", "expected_version": 1},
            format="json",
        )
        self.assertEqual(conflit.status_code, status.HTTP_409_CONFLICT)

    def test_candidature_impossible_pour_une_offre_non_publiee(self):
        opportunite = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Offre en brouillon",
            description="Pas encore publiée.",
            type=Opportunite.Type.EMPLOI,
        )
        self.client.force_authenticate(user=self.candidat)
        reponse = self.client.post(
            "/api/opportunites/candidatures/",
            {
                "opportunite": opportunite.pk,
                "message": "Je souhaite postuler.",
                "consentement_partage_profil": True,
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Candidature.objects.exists())

    def test_recherche_filtre_statut_type_contrat_ville_et_budget(self):
        correspondance = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Mission terrain",
            description="Intervention à Abidjan",
            type=Opportunite.Type.MISSION,
            statut=Opportunite.Statut.PUBLIEE,
            contrat=Opportunite.Contrat.CDD,
            ville="Abidjan",
            pays="CI",
            devise="XOF",
            budget_minimum=1000,
            budget_maximum=2000,
        )
        Opportunite.objects.create(
            createur=self.recruteur,
            titre="Emploi permanent",
            description="Autre offre",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
            contrat=Opportunite.Contrat.CDI,
            ville="Yamoussoukro",
        )
        Opportunite.objects.create(
            createur=self.recruteur,
            titre="Brouillon mission",
            description="Non publiée",
            type=Opportunite.Type.MISSION,
            statut=Opportunite.Statut.BROUILLON,
            contrat=Opportunite.Contrat.CDD,
            ville="Abidjan",
            pays="CI",
            devise="XOF",
            budget_minimum=1000,
            budget_maximum=2000,
        )
        self.client.force_authenticate(self.recruteur)

        reponse = self.client.get(
            "/api/opportunites/?statut=publiee&type=mission&contrat=cdd"
            "&ville=abidjan&pays=ci&budget_min=1500&budget_max=2500&devise=xof"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.data)
        self.assertEqual(
            [item["id"] for item in reponse.data["results"]],
            [correspondance.pk],
        )

    def test_filtres_invalides_sont_refuses(self):
        reponse = self.client.get(
            "/api/opportunites/?budget_min=2500&budget_max=1000&devise=XOF"
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detail_expose_les_libelles_de_metier_et_competences(self):
        metier = Metier.objects.create(code="gestion-projet", nom="Gestion de projet")
        competence = Competence.objects.create(nom="Planification")
        opportunite = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Cheffe de projet",
            description="Coordination d’équipe.",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
            metier=metier,
        )
        opportunite.competences.add(competence)
        self.client.force_authenticate(user=None)

        reponse = self.client.get(f"/api/v2/opportunites/{opportunite.pk}/")

        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.data)
        self.assertEqual(reponse.data["metier_nom"], "Gestion de projet")
        self.assertEqual(
            reponse.data["competences_detail"],
            [{"id": competence.pk, "nom": "Planification"}],
        )

    def test_partage_du_profil_exige_un_consentement_explicite(self):
        opportunite = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Offre publiée",
            description="Offre visible.",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
        )
        self.client.force_authenticate(user=self.candidat)

        reponse = self.client.post(
            "/api/opportunites/candidatures/",
            {
                "opportunite": opportunite.pk,
                "message": "Je souhaite postuler.",
                "consentement_partage_profil": False,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Candidature.objects.exists())

    def test_urgence_exige_une_raison_et_une_date_limite_future(self):
        self.client.force_authenticate(user=self.recruteur)
        donnees = {
            "titre": "Intervention rapide",
            "description": "Un renfort est nécessaire.",
            "type": "mission",
            "urgence": "urgente",
            "date_limite_candidature": "2099-12-31",
        }

        reponse = self.client.post(
            "/api/opportunites/",
            donnees,
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("motif_urgence", reponse.data["erreurs"])
        donnees["motif_urgence"] = "Démarrage du chantier imminent."
        reponse = self.client.post(
            "/api/opportunites/",
            donnees,
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(reponse.data["urgence"], "urgente")
        self.assertEqual(
            reponse.data["motif_urgence"],
            "Démarrage du chantier imminent.",
        )

    def test_un_utilisateur_sans_role_recruteur_ne_peut_pas_creer_une_offre(self):
        professionnel = Utilisateur.objects.create_user(
            username="professionnel@akasha.ci",
            email="professionnel@akasha.ci",
            password="mot-de-passe-pour-test",
            role_actif="professionnel",
            roles_professionnels=["professionnel"],
        )
        self.client.force_authenticate(user=professionnel)

        reponse = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Offre non autorisée",
                "description": "Cette création doit être refusée.",
                "type": "emploi",
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Opportunite.objects.filter(titre="Offre non autorisée").exists()
        )

    def test_un_utilisateur_sans_role_candidat_ne_peut_pas_postuler(self):
        opportunite = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Offre publiée",
            description="Offre visible.",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
        )
        candidat_sans_role_attribue = Utilisateur.objects.create_user(
            username="candidat-sans-role@akasha.ci",
            email="candidat-sans-role@akasha.ci",
            password="mot-de-passe-pour-test",
            role_actif="candidat",
        )
        self.client.force_authenticate(user=candidat_sans_role_attribue)

        reponse = self.client.post(
            "/api/opportunites/candidatures/",
            {"opportunite": opportunite.pk, "message": "Je postule."},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Candidature.objects.exists())

    def test_recruteur_organisation_peut_publier_et_traiter_uniquement_ses_offres(self):
        organisation = self.creer_organisation("Entreprise vérifiée")
        recruteur_organisation = Utilisateur.objects.create_user(
            username="membre-entreprise@akasha.ci",
            email="membre-entreprise@akasha.ci",
            password="mot-de-passe-pour-test",
        )
        autre_recruteur = Utilisateur.objects.create_user(
            username="autre-membre@akasha.ci",
            email="autre-membre@akasha.ci",
            password="mot-de-passe-pour-test",
        )
        autre_organisation = self.creer_organisation("Autre entreprise")
        self.ajouter_membre_organisation(
            organisation,
            recruteur_organisation,
            AppartenanceOrganisation.Role.RECRUTEUR,
        )
        self.ajouter_membre_organisation(
            autre_organisation,
            autre_recruteur,
            AppartenanceOrganisation.Role.RECRUTEUR,
        )

        self.client.force_authenticate(user=recruteur_organisation)
        creation = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Offre de l'entreprise",
                "description": "Recrutement géré par l'organisation.",
                "type": "emploi",
                "organisation": organisation.pk,
            },
            format="json",
        )
        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.data)
        self.assertEqual(creation.data["organisation"], organisation.pk)
        self.assertEqual(creation.data["organisation_nom"], organisation.nom)

        offre_id = creation.data["id"]
        self.client.force_authenticate(user=autre_recruteur)
        self.assertEqual(
            self.client.get(f"/api/opportunites/{offre_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.post(
                f"/api/opportunites/{offre_id}/publier/",
                {},
                format="json",
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.client.force_authenticate(user=recruteur_organisation)
        self.ajouter_image_opportunite(offre_id)
        publication = self.client.post(
            f"/api/opportunites/{offre_id}/publier/",
            {},
            format="json",
        )
        self.assertEqual(publication.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.candidat)
        candidature = self.client.post(
            "/api/opportunites/candidatures/",
            {
                "opportunite": offre_id,
                "message": "Ma candidature.",
                "consentement_partage_profil": True,
            },
            format="json",
        )
        self.assertEqual(candidature.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=recruteur_organisation)
        candidatures_recues = self.client.get(
            "/api/opportunites/candidatures/recues/"
        )
        self.assertEqual(candidatures_recues.status_code, status.HTTP_200_OK)
        self.assertEqual(candidatures_recues.data["count"], 1)

        self.client.force_authenticate(user=autre_recruteur)
        candidatures_autre_organisation = self.client.get(
            "/api/opportunites/candidatures/recues/"
        )
        self.assertEqual(candidatures_autre_organisation.status_code, status.HTTP_200_OK)
        self.assertEqual(candidatures_autre_organisation.data["count"], 0)

    def test_proprietaire_peut_creer_une_offre_sans_role_recruteur_global(self):
        organisation = self.creer_organisation("Entreprise propriétaire")
        proprietaire = Utilisateur.objects.create_user(
            username="proprietaire-entreprise@akasha.ci",
            email="proprietaire-entreprise@akasha.ci",
            password="mot-de-passe-pour-test",
        )
        self.ajouter_membre_organisation(
            organisation,
            proprietaire,
            AppartenanceOrganisation.Role.PROPRIETAIRE,
        )
        self.client.force_authenticate(user=proprietaire)

        reponse = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Offre du propriétaire",
                "description": "L'appartenance donne le droit de publier.",
                "type": "emploi",
                "organisation": organisation.pk,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(reponse.data["organisation"], organisation.pk)

    def test_un_membre_sans_droit_de_recrutement_ne_peut_pas_creer_une_offre(self):
        organisation = self.creer_organisation("Entreprise")
        membre = Utilisateur.objects.create_user(
            username="membre-simple@akasha.ci",
            email="membre-simple@akasha.ci",
            password="mot-de-passe-pour-test",
        )
        self.ajouter_membre_organisation(
            organisation,
            membre,
            AppartenanceOrganisation.Role.MEMBRE,
        )
        self.client.force_authenticate(user=membre)

        reponse = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Offre interdite",
                "description": "Un simple membre ne peut pas publier.",
                "type": "emploi",
                "organisation": organisation.pk,
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Opportunite.objects.filter(titre="Offre interdite").exists())

    def test_une_organisation_non_verifiee_ne_peut_pas_publier(self):
        organisation = self.creer_organisation(
            "Entreprise en attente",
            est_verifiee=False,
        )
        self.ajouter_membre_organisation(
            organisation,
            self.recruteur,
            AppartenanceOrganisation.Role.RECRUTEUR,
        )
        self.client.force_authenticate(user=self.recruteur)
        creation = self.client.post(
            "/api/opportunites/",
            {
                "titre": "Offre en attente de vérification",
                "description": "Cette offre reste un brouillon.",
                "type": "emploi",
                "organisation": organisation.pk,
            },
            format="json",
        )
        self.assertEqual(creation.status_code, status.HTTP_201_CREATED)

        publication = self.client.post(
            f"/api/opportunites/{creation.data['id']}/publier/",
            {},
            format="json",
        )

        self.assertEqual(publication.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Opportunite.objects.get(pk=creation.data["id"]).statut,
            Opportunite.Statut.BROUILLON,
        )

    def test_la_retrait_d_appartenance_revoque_l_acces_a_l_offre(self):
        organisation = self.creer_organisation("Entreprise")
        createur = Utilisateur.objects.create_user(
            username="ancien-recruteur@akasha.ci",
            email="ancien-recruteur@akasha.ci",
            password="mot-de-passe-pour-test",
        )
        appartenance = self.ajouter_membre_organisation(
            organisation,
            createur,
            AppartenanceOrganisation.Role.RECRUTEUR,
        )
        offre = Opportunite.objects.create(
            createur=createur,
            organisation=organisation,
            titre="Offre privée",
            description="Visible uniquement aux membres autorisés.",
            type=Opportunite.Type.EMPLOI,
        )
        appartenance.delete()
        self.client.force_authenticate(user=createur)

        self.assertEqual(
            self.client.get(f"/api/opportunites/{offre.pk}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_une_offre_ne_peut_pas_changer_ou_quitter_son_organisation(self):
        organisation = self.creer_organisation("Entreprise d'origine")
        autre_organisation = self.creer_organisation("Autre entreprise")
        self.ajouter_membre_organisation(
            organisation,
            self.recruteur,
            AppartenanceOrganisation.Role.RECRUTEUR,
        )
        self.ajouter_membre_organisation(
            autre_organisation,
            self.recruteur,
            AppartenanceOrganisation.Role.RECRUTEUR,
        )
        offre = Opportunite.objects.create(
            createur=self.recruteur,
            organisation=organisation,
            titre="Offre attribuée",
            description="Son organisation reste fixe.",
            type=Opportunite.Type.EMPLOI,
        )
        self.client.force_authenticate(user=self.recruteur)

        for nouvelle_organisation in (None, autre_organisation.pk):
            with self.subTest(organisation=nouvelle_organisation):
                reponse = self.client.patch(
                    f"/api/opportunites/{offre.pk}/",
                    {"organisation": nouvelle_organisation},
                    format="json",
                )
                self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        offre.refresh_from_db()
        self.assertEqual(offre.organisation_id, organisation.pk)

    def test_un_recruteur_ne_peut_pas_lire_ou_modifier_les_candidatures_d_autrui(self):
        opportunite = Opportunite.objects.create(
            createur=self.recruteur,
            titre="Offre publiée",
            description="Offre visible.",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
        )
        candidature = Candidature.objects.create(
            opportunite=opportunite,
            candidat=self.candidat,
            message="Ma candidature.",
        )
        autre_recruteur = Utilisateur.objects.create_user(
            username="autre@akasha.ci",
            email="autre@akasha.ci",
            password="test-password-for-opportunity-tests",
        )
        self.client.force_authenticate(user=autre_recruteur)
        reponse = self.client.post(
            f"/api/opportunites/candidatures/{candidature.pk}/transition/",
            {"statut": "refusee", "expected_version": 1},
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)
        candidature.refresh_from_db()
        self.assertEqual(candidature.statut, Candidature.Statut.ENVOYEE)
