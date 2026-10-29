from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    EntrepriseReference,
    EtablissementReference,
    Marche,
    ProgrammeFormationReference,
    Ville,
)

Utilisateur = get_user_model()


class ReferencesLocaliseesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.utilisateur = Utilisateur.objects.create_user(
            username="mariam@example.test",
            email="mariam@example.test",
            password="Exemple-securise-2026!",
        )
        self.client.force_authenticate(user=self.utilisateur)
        self.marche = Marche.objects.get(code_pays="CI", est_actif=True)

    def test_utilisateur_peut_ajouter_puis_rechercher_une_ville_du_pays(self):
        creation = self.client.post(
            "/api/internationalisation/villes/",
            {"nom": "Cocody", "pays": "CI"},
            format="json",
        )

        self.assertEqual(creation.status_code, status.HTTP_201_CREATED)
        self.assertEqual(creation.data["pays"], "CI")
        self.assertEqual(Ville.objects.get(pk=creation.data["id"]).cree_par, self.utilisateur)

        recherche = self.client.get(
            "/api/internationalisation/villes/?pays=CI&search=coco"
        )
        self.assertEqual(recherche.status_code, status.HTTP_200_OK)
        self.assertEqual(recherche.data["results"][0]["nom"], "Cocody")

    def test_ville_en_double_ignore_la_casse(self):
        Ville.objects.create(marche=self.marche, nom="Cocody")

        reponse = self.client.post(
            "/api/internationalisation/villes/",
            {"nom": "cocody", "pays": "CI"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ville.objects.filter(marche=self.marche).count(), 1)

    def test_utilisateur_peut_ajouter_une_entreprise_pour_son_pays(self):
        creation = self.client.post(
            "/api/internationalisation/entreprises/",
            {"nom": "Atelier Akasha", "pays": "CI"},
            format="json",
        )

        self.assertEqual(creation.status_code, status.HTTP_201_CREATED)
        self.assertEqual(creation.data["nom"], "Atelier Akasha")
        self.assertEqual(
            EntrepriseReference.objects.get(pk=creation.data["id"]).marche,
            self.marche,
        )

    def test_references_refusent_un_pays_non_active(self):
        reponse = self.client.post(
            "/api/internationalisation/entreprises/",
            {"nom": "Entreprise indisponible", "pays": "XX"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EntrepriseReference.objects.exists())

    def test_etablissement_est_declare_et_son_statut_ne_peut_pas_etre_falsifie(self):
        creation = self.client.post(
            "/api/internationalisation/etablissements/",
            {
                "nom": "Université de démonstration",
                "pays": "CI",
                "type": "universite",
                "statut_verification": "registre_confirme",
            },
            format="json",
        )

        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.data)
        self.assertEqual(creation.data["statut_verification"], "declaree")
        etablissement = EtablissementReference.objects.get(pk=creation.data["id"])
        self.assertEqual(etablissement.statut_verification, "declaree")

    def test_programme_reference_se_lie_a_un_etablissement_de_meme_pays(self):
        etablissement = EtablissementReference.objects.create(
            marche=self.marche,
            nom="Institut de démonstration",
            type=EtablissementReference.Type.ECOLE,
        )

        creation = self.client.post(
            "/api/internationalisation/programmes-formation/",
            {
                "intitule": "Formation de démonstration",
                "niveau": "Licence",
                "pays": "CI",
                "etablissement": etablissement.pk,
            },
            format="json",
        )

        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.data)
        self.assertEqual(creation.data["statut_verification"], "declaree")
        self.assertEqual(
            ProgrammeFormationReference.objects.get(pk=creation.data["id"]).etablissement,
            etablissement,
        )
