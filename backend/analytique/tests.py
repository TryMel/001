from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from comptes.models import Utilisateur
from .models import EvenementInteraction


class InteractionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.utilisateur = Utilisateur.objects.create_user(
            username="candidat@akasha.test",
            email="candidat@akasha.test",
            password="MotDePasseSecurise2026!",
            role_actif="candidat",
            roles_professionnels=["candidat", "client"],
        )
        self.client.force_authenticate(user=self.utilisateur)

    def test_enregistre_la_fonctionnalite_et_le_role_actif_sans_identite(self):
        reponse = self.client.post(
            "/api/analytique/evenements/",
            {"fonctionnalite": "opportunites", "role_actif": "client"},
            format="json",
        )

        self.assertEqual(reponse.status_code, 204)
        evenement = EvenementInteraction.objects.get()
        self.assertEqual(evenement.fonctionnalite, "opportunites")
        self.assertEqual(evenement.role_actif, "candidat")
        self.assertFalse(hasattr(evenement, "utilisateur_id"))

    def test_suivi_du_changement_est_associe_au_nouvel_espace(self):
        changement = self.client.patch(
            "/api/comptes/moi/role-actif/",
            {"role_actif": "client"},
            format="json",
        )
        self.assertEqual(changement.status_code, 200)

        suivi = self.client.post(
            "/api/analytique/evenements/",
            {"fonctionnalite": "changement_role"},
            format="json",
        )

        self.assertEqual(suivi.status_code, 204)
        evenement = EvenementInteraction.objects.get()
        self.assertEqual(evenement.role_actif, "client")

    def test_refuse_les_fonctionnalites_inconnues(self):
        reponse = self.client.post(
            "/api/analytique/evenements/",
            {"fonctionnalite": "mot_de_passe"},
            format="json",
        )

        self.assertEqual(reponse.status_code, 400)
        self.assertFalse(EvenementInteraction.objects.exists())

    def test_exige_un_compte_authentifie(self):
        self.client.force_authenticate(user=None)

        reponse = self.client.post(
            "/api/analytique/evenements/",
            {"fonctionnalite": "accueil"},
            format="json",
        )

        self.assertEqual(reponse.status_code, 401)

    def test_refuse_un_role_actif_non_reconnu(self):
        self.utilisateur.role_actif = "espace_inconnu"
        self.utilisateur.roles_professionnels = ["espace_inconnu"]
        self.utilisateur.save(update_fields=("role_actif", "roles_professionnels"))

        reponse = self.client.post(
            "/api/analytique/evenements/",
            {"fonctionnalite": "accueil"},
            format="json",
        )

        self.assertEqual(reponse.status_code, 400)
        self.assertFalse(EvenementInteraction.objects.exists())

    @override_settings(ANALYTICS_RETENTION_DAYS=365)
    def test_purge_uniquement_les_evenements_plus_anciens_que_la_retention(self):
        ancien = EvenementInteraction.objects.create(
            fonctionnalite="accueil",
            role_actif="candidat",
        )
        recent = EvenementInteraction.objects.create(
            fonctionnalite="profil",
            role_actif="candidat",
        )
        EvenementInteraction.objects.filter(pk=ancien.pk).update(
            cree_le=timezone.now() - timedelta(days=366)
        )

        call_command("purger_evenements_analytiques", verbosity=0)

        self.assertFalse(EvenementInteraction.objects.filter(pk=ancien.pk).exists())
        self.assertTrue(EvenementInteraction.objects.filter(pk=recent.pk).exists())
