from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import RegleCommission


class RegleCommissionTests(TestCase):
    def test_migration_cree_la_commission_initiale_de_dix_sept_pour_cent(self):
        regle = RegleCommission.objects.get(active=True)

        self.assertEqual(regle.version, 1)
        self.assertEqual(regle.taux_pourcentage, Decimal("17.00"))

    def test_une_nouvelle_version_peut_etre_preparee_sans_modifier_l_historique(self):
        regle_initiale = RegleCommission.objects.get(active=True)
        nouvelle_regle = RegleCommission.objects.create(
            version=2,
            taux_pourcentage=Decimal("18.50"),
        )

        self.assertFalse(nouvelle_regle.active)
        regle_initiale.refresh_from_db()
        self.assertEqual(regle_initiale.taux_pourcentage, Decimal("17.00"))
        self.assertTrue(regle_initiale.active)

    def test_la_base_refuse_deux_regles_actives(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegleCommission.objects.create(
                version=2,
                taux_pourcentage=Decimal("18.50"),
                active=True,
            )

    def test_la_base_refuse_un_taux_superieur_a_cent_pour_cent(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegleCommission.objects.create(
                version=2,
                taux_pourcentage=Decimal("100.01"),
            )

    def test_un_administrateur_peut_activer_une_nouvelle_version(self):
        administrateur = get_user_model().objects.create_superuser(
            username="admin@akasha.test",
            email="admin@akasha.test",
            password="Test-Admin-Password-2026!",
        )
        nouvelle_regle = RegleCommission.objects.create(
            version=2,
            taux_pourcentage=Decimal("18.50"),
        )
        self.client.force_login(administrateur)

        reponse = self.client.post(
            "/administration/facturation/reglecommission/",
            {
                "action": "activer_regle",
                "index": "0",
                "_selected_action": [str(nouvelle_regle.pk)],
            },
            follow=True,
        )

        self.assertEqual(
            reponse.status_code,
            200,
            f"POST admin redirigé vers {reponse.get('Location')}",
        )
        self.assertEqual(
            RegleCommission.objects.filter(active=True).values_list(
                "version", flat=True
            ).get(),
            2,
        )
        nouvelle_regle.refresh_from_db()
        self.assertEqual(nouvelle_regle.activee_par, administrateur)
        self.assertIsNotNone(nouvelle_regle.effective_le)
