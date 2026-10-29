from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings

from collaborations.models import DemandeService, Proposition
from opportunites.models import Candidature, Opportunite


Utilisateur = get_user_model()
MOT_DE_PASSE = "Akasha-Local-Demo-2026!"


class ChargerDonneesDemoTests(TestCase):
    def lancer_commande(self, **options):
        return call_command(
            "charger_donnees_demo",
            confirm_local_development_db=True,
            password=MOT_DE_PASSE,
            stdout=StringIO(),
            **options,
        )

    def test_cree_les_comptes_et_parcours_de_demo_de_facon_idempotente(self):
        with override_settings(DEBUG=True):
            self.lancer_commande()
            self.lancer_commande()

        self.assertEqual(
            Utilisateur.objects.filter(email__endswith="@demo.akasha.local").count(),
            6,
        )
        self.assertTrue(
            Utilisateur.objects.get(
                email="recruteur@demo.akasha.local"
            ).check_password(MOT_DE_PASSE)
        )
        self.assertEqual(
            Opportunite.objects.filter(titre__startswith="Démo -").count(),
            2,
        )
        self.assertTrue(
            Opportunite.objects.filter(
                titre="Démo - Recrutement de l'entreprise",
                organisation__nom="Entreprise Démo Akasha",
                statut=Opportunite.Statut.BROUILLON,
            ).exists()
        )
        self.assertEqual(
            Candidature.objects.filter(
                opportunite__titre__startswith="Démo -"
            ).count(),
            1,
        )
        self.assertEqual(
            DemandeService.objects.filter(titre__startswith="Démo -").count(),
            2,
        )
        self.assertEqual(
            Proposition.objects.filter(
                demande__titre="Démo - Réparer une fuite d'eau"
            ).count(),
            1,
        )

    def test_refuse_la_base_si_debug_est_desactive(self):
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command(
                    "charger_donnees_demo",
                    confirm_local_development_db=True,
                    password=MOT_DE_PASSE,
                    stdout=StringIO(),
                )

    def test_refuse_de_se_lancer_sans_confirmation_de_base_locale(self):
        with self.assertRaises(CommandError):
            call_command(
                "charger_donnees_demo",
                password=MOT_DE_PASSE,
                stdout=StringIO(),
            )
