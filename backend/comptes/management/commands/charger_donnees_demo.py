from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from collaborations.models import DemandeService, OffreService, Proposition
from organisations.models import AppartenanceOrganisation, Organisation
from opportunites.models import Candidature, HistoriqueCandidature, Opportunite
from profils.models import ProfilProfessionnel
from referentiel.models import Competence, Metier


class Command(BaseCommand):
    help = "Crée des comptes et parcours fictifs pour tester Akasha en développement."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-local-development-db",
            action="store_true",
            help="Confirme que la base configurée est une base locale de développement.",
        )
        parser.add_argument(
            "--password",
            required=True,
            help="Mot de passe commun des comptes démo.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Les données démo sont interdites lorsque DEBUG=False.")
        if not options["confirm_local_development_db"]:
            raise CommandError(
                "Confirmez la base de développement avec "
                "--confirm-local-development-db."
            )

        base = settings.DATABASES["default"]
        moteur = base["ENGINE"]
        hote = (base.get("HOST") or "").lower()
        if moteur.endswith("postgresql") and hote not in (
            "",
            "localhost",
            "127.0.0.1",
            "::1",
        ):
            raise CommandError(
                "La base PostgreSQL n'est pas locale ; aucune donnée démo n'a été créée."
            )
        if not (moteur.endswith("postgresql") or moteur.endswith("sqlite3")):
            raise CommandError(
                "La commande démo accepte uniquement PostgreSQL local ou SQLite."
            )

        mot_de_passe = options["password"]
        if len(mot_de_passe) < 12:
            raise CommandError("Le mot de passe démo doit contenir au moins 12 caractères.")

        with transaction.atomic():
            utilisateurs = self._creer_utilisateurs(mot_de_passe)
            metier = self._creer_referentiel()
            self._creer_profils(utilisateurs, metier)
            organisation = self._creer_organisation(utilisateurs["organisation"])
            self._creer_opportunite_et_candidature(
                utilisateurs["recruteur"],
                utilisateurs["candidat"],
                metier,
            )
            self._creer_brouillon_organisation(
                utilisateurs["organisation"],
                organisation,
                metier,
            )
            self._creer_demandes(
                utilisateurs["client"],
                utilisateurs["professionnel"],
            )
            self._creer_offre_service(utilisateurs["professionnel"])

        self.stdout.write(self.style.SUCCESS("Parcours fictifs Akasha créés ou déjà présents."))
        self.stdout.write(f"Organisation de démonstration : {organisation.nom} (non vérifiée)")
        self.stdout.write("Comptes démo :")
        for utilisateur in utilisateurs.values():
            self.stdout.write(f"  {utilisateur.email} / {mot_de_passe}")

    def _creer_utilisateurs(self, mot_de_passe):
        utilisateur_model = get_user_model()
        definitions = {
            "client": ("client@demo.akasha.local", "Aïssata", "Client", ["client"]),
            "professionnel": (
                "professionnel@demo.akasha.local",
                "Koffi",
                "Professionnel",
                ["professionnel"],
            ),
            "candidat": ("candidat@demo.akasha.local", "Yao", "Candidat", ["candidat"]),
            "etudiant": ("etudiant@demo.akasha.local", "Mariam", "Étudiante", ["etudiant"]),
            "recruteur": (
                "recruteur@demo.akasha.local",
                "Nadia",
                "Recruteuse",
                ["recruteur"],
            ),
            "organisation": (
                "organisation@demo.akasha.local",
                "Équipe",
                "Démo",
                ["organisation"],
            ),
        }
        utilisateurs = {}
        for cle, (email, prenom, nom, roles) in definitions.items():
            utilisateur = utilisateur_model.objects.filter(email=email).first()
            if utilisateur is not None and (
                utilisateur.username != email
                or utilisateur.is_staff
                or utilisateur.is_superuser
            ):
                raise CommandError(
                    f"Le compte {email} existe déjà et n'est pas un compte démo géré."
                )
            if utilisateur is None:
                utilisateur = utilisateur_model(
                    username=email,
                    email=email,
                )

            utilisateur.first_name = prenom
            utilisateur.last_name = nom
            utilisateur.role_actif = roles[0]
            utilisateur.roles_professionnels = roles
            utilisateur.onboarding_termine = True
            utilisateur.is_active = True
            utilisateur.set_password(mot_de_passe)
            utilisateur.save()
            utilisateurs[cle] = utilisateur
        return utilisateurs

    def _creer_referentiel(self):
        metier, _ = Metier.objects.get_or_create(
            code="DEMO-PLOMBERIE",
            defaults={"nom": "Plombier"},
        )
        competence, _ = Competence.objects.get_or_create(
            nom="Plomberie sanitaire",
        )
        competence.metiers.add(metier)
        return metier

    def _creer_profils(self, utilisateurs, metier):
        professionnel, _ = ProfilProfessionnel.objects.get_or_create(
            utilisateur=utilisateurs["professionnel"],
            defaults={
                "titre": "Plombier professionnel",
                "biographie": (
                    "Interventions de plomberie résidentielle, entretien et dépannage."
                ),
                "ville": "Abidjan",
                "disponible": True,
                "visible_publiquement": True,
                "metier": metier,
            },
        )
        candidat, _ = ProfilProfessionnel.objects.get_or_create(
            utilisateur=utilisateurs["candidat"],
            defaults={
                "titre":                 "Candidat en plomberie",
                "biographie": "Profil fictif pour tester les candidatures.",
                "ville": "Abidjan",
                "visible_publiquement": True,
            },
        )
        etudiant, _ = ProfilProfessionnel.objects.get_or_create(
            utilisateur=utilisateurs["etudiant"],
            defaults={
                "titre":                 "Étudiante en plomberie",
                "biographie": "Portfolio fictif pour tester le parcours étudiant.",
                "ville": "Abidjan",
                "visible_publiquement": True,
            },
        )
        self._attacher_photo(professionnel, "photo", "demo-professionnel.png", (42, 135, 118))
        self._attacher_photo(candidat, "photo", "demo-candidat.png", (71, 93, 178))
        self._attacher_photo(etudiant, "photo", "demo-etudiant.png", (194, 118, 55))

    def _creer_organisation(self, proprietaire):
        organisation, _ = Organisation.objects.get_or_create(
            nom="Entreprise Démo Akasha",
            defaults={
                "description": "Organisation fictive réservée aux essais locaux.",
                "ville": "Abidjan",
                "pays": "CI",
                "est_verifiee": False,
            },
        )
        AppartenanceOrganisation.objects.get_or_create(
            organisation=organisation,
            utilisateur=proprietaire,
            defaults={"role": AppartenanceOrganisation.Role.PROPRIETAIRE},
        )
        self._attacher_photo(organisation, "photo", "demo-organisation.png", (35, 76, 121))
        return organisation

    def _creer_opportunite_et_candidature(self, recruteur, candidat, metier):
        opportunite, _ = Opportunite.objects.get_or_create(
            createur=recruteur,
            titre="Démo - Assistant plombier en formation",
            defaults={
                "description": (
                    "Participer au suivi de chantier, aux métrés et à la coordination "
                    "des équipes. Offre fictive pour tester la recherche et la candidature."
                ),
                "type": Opportunite.Type.STAGE,
                "statut": Opportunite.Statut.PUBLIEE,
                "ville": "Abidjan",
                "pays": "CI",
                "budget_minimum": 100000,
                "budget_maximum": 150000,
                "devise": "XOF",
                "duree": "3 mois",
                "metier": metier,
            },
        )
        candidature, creee = Candidature.objects.get_or_create(
            opportunite=opportunite,
            candidat=candidat,
            defaults={"message": "Candidature de démonstration."},
        )
        if creee:
            HistoriqueCandidature.objects.create(
                candidature=candidature,
                acteur=candidat,
                nouveau_statut=candidature.statut,
            )
        self._attacher_image_contenu(
            opportunite,
            "demo-opportunite-assistant-plombier.png",
            (38, 119, 137),
        )

    def _creer_brouillon_organisation(self, proprietaire, organisation, metier):
        opportunite, _ = Opportunite.objects.get_or_create(
            createur=proprietaire,
            titre="Démo - Recrutement de l'entreprise",
            defaults={
                "organisation": organisation,
                "description": (
                    "Brouillon fictif pour tester l'accès aux offres de l'entreprise. "
                    "La publication attend la vérification de l'organisation."
                ),
                "type": Opportunite.Type.EMPLOI,
                "statut": Opportunite.Statut.BROUILLON,
                "ville": organisation.ville,
                "pays": organisation.pays,
                "metier": metier,
            },
        )
        self._attacher_image_contenu(
            opportunite,
            "demo-opportunite-entreprise.png",
            (95, 79, 155),
        )

    def _creer_demandes(self, client, professionnel):
        demande_ouverte, _ = DemandeService.objects.get_or_create(
            client=client,
            titre="Démo - Réparer une fuite d'eau",
            defaults={
                "description": (
                    "Recherche d'un professionnel pour localiser et réparer une fuite "
                    "dans une cuisine. Demande fictive."
                ),
                "ville": "Abidjan",
                "pays": "CI",
                "budget_minimum": 20000,
                "budget_maximum": 50000,
                "devise": "XOF",
                "statut": DemandeService.Statut.OUVERTE,
                "publie_le": timezone.now(),
            },
        )
        demande_ouverte.competences.add(
            Competence.objects.get(nom="Plomberie sanitaire")
        )
        self._attacher_photo(
            demande_ouverte,
            "photo",
            "demo-demande-fuite.png",
            (33, 125, 104),
        )

        demande_secondaire, _ = DemandeService.objects.get_or_create(
            client=client,
            titre="Démo - Installer un chauffe-eau",
            defaults={
                "description": (
                    "Installation et mise en service d'un chauffe-eau dans un logement."
                ),
                "ville": "Cocody",
                "pays": "CI",
                "budget_maximum": 80000,
                "devise": "XOF",
                "statut": DemandeService.Statut.OUVERTE,
                "publie_le": timezone.now(),
            },
        )
        demande_secondaire.competences.add(
            Competence.objects.get(nom="Plomberie sanitaire")
        )
        self._attacher_photo(
            demande_secondaire,
            "photo",
            "demo-demande-chauffe-eau.png",
            (186, 93, 53),
        )

        proposition_existante = Proposition.objects.filter(
            demande=demande_ouverte,
            prestataire=professionnel,
        ).first()
        if proposition_existante is None:
            Proposition.objects.create(
                demande=demande_ouverte,
                prestataire=professionnel,
                montant=35000,
                devise="XOF",
                delai_jours=2,
                message=(
                    "Je peux intervenir sous deux jours et fournir un devis détaillé."
                ),
            )

    def _creer_offre_service(self, professionnel):
        profil = ProfilProfessionnel.objects.get(utilisateur=professionnel)
        offre, _ = OffreService.objects.get_or_create(
            profil=profil,
            titre="Demo - Depannage plomberie a domicile",
            defaults={
                "description": (
                    "Recherche de fuite, depannage et petites installations sanitaires. "
                    "Offre fictive pour explorer le parcours prestataire."
                ),
                "ville": "Abidjan",
                "pays": "CI",
                "tarification": OffreService.Tarification.SUR_DEVIS,
                "devise": "XOF",
                "statut": OffreService.Statut.PUBLIEE,
            },
        )
        offre.competences.add(Competence.objects.get(nom="Plomberie sanitaire"))
        self._attacher_photo(
            offre,
            "photo",
            "demo-service-plomberie.png",
            (36, 102, 173),
        )

    def _attacher_image_contenu(self, objet, nom, couleur):
        if objet.images.exists():
            return
        objet.images.create(
            fichier=ContentFile(self._image_demo(couleur), name=nom),
            position=0,
        )

    def _attacher_photo(self, objet, champ, nom, couleur):
        if getattr(objet, champ):
            return
        getattr(objet, champ).save(
            nom,
            ContentFile(self._image_demo(couleur), name=nom),
            save=False,
        )
        objet.save(update_fields=(champ,))

    @staticmethod
    def _image_demo(couleur):
        """Illustration locale deterministe, sans telechargement ni donnees tierces."""
        image = Image.new("RGB", (960, 540), couleur)
        dessin = ImageDraw.Draw(image)
        clair = tuple(min(255, composante + 55) for composante in couleur)
        sombre = tuple(max(0, composante - 35) for composante in couleur)
        dessin.ellipse((580, -120, 1060, 360), fill=clair)
        dessin.rounded_rectangle((72, 315, 680, 450), radius=26, fill=sombre)
        dessin.ellipse((140, 105, 365, 330), fill=(245, 247, 250))
        sortie = BytesIO()
        image.save(sortie, format="PNG", optimize=True)
        return sortie.getvalue()
