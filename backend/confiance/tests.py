from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from collaborations.models import Collaboration, DemandeService, Proposition
from profils.models import ProfilProfessionnel

from .models import Evaluation

Utilisateur = get_user_model()


class EvaluationsTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.client_user = Utilisateur.objects.create_user(
            username="client@example.test",
            email="client@example.test",
            password="local-test-password",
            roles_professionnels=["client"],
            role_actif="client",
        )
        self.pro_user = Utilisateur.objects.create_user(
            username="pro@example.test",
            email="pro@example.test",
            password="local-test-password",
            roles_professionnels=["professionnel"],
            role_actif="professionnel",
            onboarding_termine=True,
        )
        self.profil = ProfilProfessionnel.objects.create(
            utilisateur=self.pro_user,
            visible_publiquement=True,
        )
        self.demande = DemandeService.objects.create(
            client=self.client_user,
            titre="Création de site",
            description="Site vitrine.",
            statut=DemandeService.Statut.ATTRIBUEE,
        )
        self.proposition = Proposition.objects.create(
            demande=self.demande,
            prestataire=self.pro_user,
            montant=10000,
            delai_jours=7,
            message="Je réalise ce projet.",
            statut=Proposition.Statut.ACCEPTEE,
        )
        self.collaboration = Collaboration.objects.create(
            demande=self.demande,
            proposition=self.proposition,
            client=self.client_user,
            prestataire=self.pro_user,
            perimetre="Site vitrine",
            montant=10000,
            statut=Collaboration.Statut.TERMINEE,
        )

    def test_avis_public_seulement_apres_collaboration_terminee(self):
        self.client_api.force_authenticate(user=self.client_user)
        reponse = self.client_api.post(
            "/api/confiance/evaluations/",
            {
                "evalue": self.pro_user.pk,
                "collaboration": self.collaboration.pk,
                "note": 5,
                "commentaire": "Travail soigné.",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(reponse.data["statut"], Evaluation.Statut.PUBLIEE)

        public = self.client_api.get(
            f"/api/confiance/professionnels/{self.profil.pk}/evaluations/"
        )
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        self.assertEqual(public.data["nombre"], 1)
        self.assertIsNone(public.data["moyenne"])
        self.assertEqual(public.data["message"], "Pas encore assez d’avis")
        self.assertEqual(public.data["seuil"], 5)
        self.assertEqual(public.data["resultats"][0]["note"], 5)

    def test_score_public_transparent_apres_cinq_collaborations_verifiees(self):
        Evaluation.objects.create(
            evalue=self.pro_user,
            auteur=self.client_user,
            collaboration=self.collaboration,
            note=5,
        )
        for index, note in enumerate((4, 3, 5, 3), start=1):
            demande = DemandeService.objects.create(
                client=self.client_user,
                titre=f"Mission {index}",
                description="Mission terminée.",
                statut=DemandeService.Statut.ATTRIBUEE,
            )
            proposition = Proposition.objects.create(
                demande=demande,
                prestataire=self.pro_user,
                montant=10000,
                delai_jours=7,
                message="Mission acceptée.",
                statut=Proposition.Statut.ACCEPTEE,
            )
            collaboration = Collaboration.objects.create(
                demande=demande,
                proposition=proposition,
                client=self.client_user,
                prestataire=self.pro_user,
                perimetre="Mission terminée",
                montant=10000,
                statut=Collaboration.Statut.TERMINEE,
            )
            Evaluation.objects.create(
                evalue=self.pro_user,
                auteur=self.client_user,
                collaboration=collaboration,
                note=note,
            )

        reponse = self.client_api.get(
            f"/api/confiance/professionnels/{self.profil.pk}/evaluations/"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["nombre"], 5)
        self.assertEqual(reponse.data["moyenne"], 4.0)
        self.assertIsNone(reponse.data["message"])
        self.assertEqual(set(reponse.data["periode"]), {"debut", "fin"})

    def test_avis_lies_a_une_collaboration_non_terminee_ne_comptent_pas(self):
        demande = DemandeService.objects.create(
            client=self.client_user,
            titre="Mission en cours",
            description="Mission non terminée.",
            statut=DemandeService.Statut.ATTRIBUEE,
        )
        proposition = Proposition.objects.create(
            demande=demande,
            prestataire=self.pro_user,
            montant=10000,
            delai_jours=7,
            message="Mission acceptée.",
            statut=Proposition.Statut.ACCEPTEE,
        )
        collaboration_en_cours = Collaboration.objects.create(
            demande=demande,
            proposition=proposition,
            client=self.client_user,
            prestataire=self.pro_user,
            perimetre="Mission en cours",
            montant=10000,
            statut=Collaboration.Statut.EN_COURS,
        )
        Evaluation.objects.create(
            evalue=self.pro_user,
            auteur=self.client_user,
            collaboration=collaboration_en_cours,
            note=5,
        )

        reponse = self.client_api.get(
            f"/api/confiance/professionnels/{self.profil.pk}/evaluations/"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["nombre"], 0)
        self.assertIsNone(reponse.data["moyenne"])
        self.assertEqual(reponse.data["message"], "Pas encore assez d’avis")

    def test_route_publique_v2_expose_la_meme_indisponibilite_sans_score(self):
        reponse = self.client_api.get(
            f"/api/v2/confiance/professionnels/{self.profil.pk}/evaluations/"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["nombre"], 0)
        self.assertIsNone(reponse.data["moyenne"])
        self.assertEqual(reponse.data["message"], "Pas encore assez d’avis")

    def test_auto_evaluation_note_invalide_et_doublon_sont_refuses(self):
        self.client_api.force_authenticate(user=self.client_user)
        base = {
            "evalue": self.pro_user.pk,
            "collaboration": self.collaboration.pk,
            "note": 5,
        }
        self.assertEqual(
            self.client_api.post(
                "/api/confiance/evaluations/",
                {**base, "evalue": self.client_user.pk},
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client_api.post(
                "/api/confiance/evaluations/",
                {**base, "note": 8},
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        premier = self.client_api.post(
            "/api/confiance/evaluations/",
            base,
            format="json",
        )
        self.assertEqual(premier.status_code, status.HTTP_201_CREATED)
        doublon = self.client_api.post(
            "/api/confiance/evaluations/",
            base,
            format="json",
        )
        self.assertEqual(doublon.status_code, status.HTTP_400_BAD_REQUEST)

    def test_avis_ne_peut_pas_etre_modifie_ou_supprime_par_le_client(self):
        evaluation = Evaluation.objects.create(
            evalue=self.pro_user,
            auteur=self.client_user,
            collaboration=self.collaboration,
            note=4,
        )
        self.client_api.force_authenticate(user=self.client_user)
        self.assertEqual(
            self.client_api.patch(
                f"/api/confiance/evaluations/{evaluation.pk}/",
                {"note": 1},
                format="json",
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client_api.delete(
                f"/api/confiance/evaluations/{evaluation.pk}/"
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_signalement_d_un_avis_est_cible_etat_non_mutable(self):
        evaluation = Evaluation.objects.create(
            evalue=self.pro_user,
            auteur=self.client_user,
            collaboration=self.collaboration,
            note=4,
        )
        self.client_api.force_authenticate(user=self.pro_user)
        reponse = self.client_api.post(
            "/api/confiance/signalements/",
            {
                "evaluation": evaluation.pk,
                "motif": "contenu",
                "description": "Je conteste ce commentaire.",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.data)
        self.assertEqual(reponse.data["statut"], "ouvert")
        self.assertEqual(
            self.client_api.patch(
                f"/api/confiance/signalements/{reponse.data['id']}/",
                {"statut": "traite"},
                format="json",
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
