import json
from datetime import timedelta
from types import SimpleNamespace

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from analytique.models import EvenementInteraction
from comptes.models import Utilisateur
from opportunites.models import Candidature, Opportunite
from configuration.parametres import _lire_configuration_securite
from configuration.exceptions import gestionnaire_exceptions
from configuration.tableau_bord import tableau_bord


class ConfigurationSecuriteTests(TestCase):
    def test_refuse_un_secret_absent(self):
        with self.assertRaises(ImproperlyConfigured):
            _lire_configuration_securite({})

    def test_refuse_le_secret_de_developpement_meme_avec_debug(self):
        with self.assertRaises(ImproperlyConfigured):
            _lire_configuration_securite(
                {
                    "SECRET_KEY": "cle-developpement-a-remplacer-immediatement",
                    "DEBUG": "True",
                }
            )

    def test_debug_est_desactive_par_defaut_avec_un_secret_configure(self):
        secret, debug = _lire_configuration_securite(
            {"SECRET_KEY": "cle-personnalisee"}
        )

        self.assertEqual(secret, "cle-personnalisee")
        self.assertFalse(debug)

    def test_debug_peut_etre_active_explicitement(self):
        _, debug = _lire_configuration_securite(
            {"SECRET_KEY": "cle-personnalisee", "DEBUG": "True"}
        )

        self.assertTrue(debug)


class TableauBordTests(TestCase):
    def test_kpi_courbes_et_clics_par_role_sont_calcules_depuis_les_donnees(self):
        maintenant = timezone.now()
        candidat = Utilisateur.objects.create_user(
            username="candidat@akasha.test",
            email="candidat@akasha.test",
            password="MotDePasseSecurise2026!",
            role_actif="candidat",
            roles_professionnels=["candidat"],
            last_login=maintenant,
        )
        ancien = Utilisateur.objects.create_user(
            username="ancien@akasha.test",
            email="ancien@akasha.test",
            password="MotDePasseSecurise2026!",
            role_actif="recruteur",
            roles_professionnels=["recruteur"],
            last_login=maintenant - timedelta(days=31),
        )
        Utilisateur.objects.filter(pk=ancien.pk).update(
            date_joined=maintenant - timedelta(days=31)
        )
        opportunite = Opportunite.objects.create(
            createur=candidat,
            titre="Développeur mobile",
            description="Offre de test",
            type=Opportunite.Type.EMPLOI,
            statut=Opportunite.Statut.PUBLIEE,
        )
        Candidature.objects.create(
            opportunite=opportunite,
            candidat=candidat,
            message="Candidature de test",
        )
        EvenementInteraction.objects.create(
            fonctionnalite="opportunites",
            role_actif="candidat",
        )

        contexte = tableau_bord(SimpleNamespace(user=candidat), {})
        indicateurs = {item["libelle"]: item["valeur"] for item in contexte["indicateurs"]}
        courbe = json.loads(contexte["graphe_activite"])
        ligne_opportunites = next(
            ligne
            for ligne in contexte["lignes_fonctionnalites"]
            if ligne["libelle"] == "Opportunités"
        )

        self.assertEqual(indicateurs["Utilisateurs actifs (30 j)"], 1)
        self.assertEqual(indicateurs["Clics mesurés (30 j)"], 1)
        self.assertEqual(indicateurs["Candidatures (30 j)"], 1)
        self.assertEqual(indicateurs["Opportunités publiées"], 1)
        self.assertEqual(courbe["datasets"][0]["data"][-1], 1)
        self.assertEqual(courbe["datasets"][1]["data"][-1], 1)
        self.assertEqual(courbe["datasets"][2]["data"][-1], 1)
        clics_par_role = {
            role["libelle"]: role["valeur"] for role in ligne_opportunites["roles"]
        }
        self.assertEqual(clics_par_role["Candidat"], 1)
        self.assertEqual(clics_par_role["Recruteur"], 0)


class TableauBordAdminTests(TestCase):
    def test_admin_affiche_les_graphiques_et_la_matrice_d_usage(self):
        administrateur = Utilisateur.objects.create_superuser(
            username="admin@akasha.test",
            email="admin@akasha.test",
            password="MotDePasseSecurise2026!",
        )
        self.client.force_login(administrateur)

        reponse = self.client.get("/administration/")

        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Activité quotidienne")
        self.assertContains(reponse, "Clics par fonctionnalité et espace")
        self.assertContains(reponse, 'class="chart"')
        self.assertContains(reponse, "365 jours")

    def test_admin_peut_ouvrir_les_listes_utilisateurs_et_organisations(self):
        mot_de_passe = "Test-administration-2026!"
        administrateur = Utilisateur.objects.create_superuser(
            username="admin-listes@akasha.test",
            email="admin-listes@akasha.test",
            password=mot_de_passe,
        )
        connexion = self.client.post(
            "/administration/login/",
            {"username": administrateur.email, "password": mot_de_passe},
        )
        self.assertEqual(connexion.status_code, 302)

        utilisateurs = self.client.get("/administration/comptes/utilisateur/")
        organisations = self.client.get(
            "/administration/organisations/organisation/"
        )

        self.assertEqual(utilisateurs.status_code, 200)
        self.assertEqual(organisations.status_code, 200)


class ApiAdministrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.administrateur = Utilisateur.objects.create_user(
            username="staff-api@akasha.test",
            email="staff-api@akasha.test",
            is_staff=True,
        )
        self.compte_standard = Utilisateur.objects.create_user(
            username="compte-api@akasha.test",
            email="compte-api@akasha.test",
        )

    def test_tableau_de_bord_est_protege_et_versionne_sur_les_deux_apis(self):
        for version in ("v1", "v2"):
            with self.subTest(version=version):
                url = f"/api/{version}/administration/overview/"
                self.client.force_authenticate(user=None)
                self.assertEqual(self.client.get(url).status_code, 401)

                self.client.force_authenticate(self.compte_standard)
                self.assertEqual(self.client.get(url).status_code, 403)

                self.client.force_authenticate(self.administrateur)
                reponse = self.client.get(url)

                self.assertEqual(reponse.status_code, 200, reponse.data)
                self.assertEqual(reponse.data["version"], version)
                self.assertEqual(reponse.data["comptes"], 2)
                self.assertEqual(reponse.data["profils_visibles"], 0)
                self.assertEqual(
                    set(reponse.data),
                    {
                        "version",
                        "comptes",
                        "profils_visibles",
                        "opportunites_publiees",
                        "organisations_a_verifier",
                        "verifications_en_attente",
                        "signalements_ouverts",
                    },
                )


class GestionErreursApiTests(TestCase):
    def test_exception_interne_est_journalisee_sans_fuite_dans_la_reponse(self):
        requete = SimpleNamespace(path="/api/exemple/")
        try:
            raise RuntimeError("internal-diagnostic-only")
        except RuntimeError as erreur:
            with self.assertLogs("django.request", level="ERROR") as journal:
                reponse = gestionnaire_exceptions(
                    erreur,
                    {"request": requete},
                )

        self.assertEqual(reponse.status_code, 500)
        self.assertEqual(reponse.data["code"], "erreur_interne")
        self.assertNotIn("internal-diagnostic-only", str(reponse.data))
        self.assertRegex(reponse.data["request_id"], r"^[0-9a-f]{32}$")
        self.assertIn("Unhandled API exception", journal.output[0])
