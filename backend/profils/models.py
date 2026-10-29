from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from referentiel.models import Competence, Metier


class ProfilProfessionnel(models.Model):
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil")
    titre = models.CharField(max_length=180, blank=True)
    biographie = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to="profils/avatars/", null=True, blank=True)
    disponible = models.BooleanField(default=True)
    visible_publiquement = models.BooleanField(default=False)
    metier = models.ForeignKey(Metier, null=True, blank=True, on_delete=models.SET_NULL)
    competences = models.ManyToManyField(Competence, through="NiveauCompetence", blank=True)


class NiveauCompetence(models.Model):
    class Niveau(models.TextChoices): DEBUTANT = "debutant", "Débutant"; AUTONOME = "autonome", "Autonome"; EXPERT = "expert", "Expert"
    profil = models.ForeignKey(ProfilProfessionnel, on_delete=models.CASCADE)
    competence = models.ForeignKey(
        Competence,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    competence_personnalisee = models.CharField(max_length=150, blank=True)
    niveau = models.CharField(max_length=12, choices=Niveau.choices, default=Niveau.AUTONOME)
    preuve = models.URLField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("profil", "competence"),
                condition=Q(competence__isnull=False),
                name="niveau_competence_reference_unique_par_profil",
            ),
            models.UniqueConstraint(
                Lower("competence_personnalisee"),
                "profil",
                condition=~Q(competence_personnalisee=""),
                name="niveau_competence_personnalisee_unique_par_profil",
            ),
            models.CheckConstraint(
                condition=(
                    Q(competence__isnull=False, competence_personnalisee="")
                    | Q(competence__isnull=True) & ~Q(competence_personnalisee="")
                ),
                name="niveau_competence_reference_ou_personnalisee",
            ),
        ]


class DisponibiliteProfil(models.Model):
    profil = models.OneToOneField(
        ProfilProfessionnel,
        on_delete=models.CASCADE,
        related_name="disponibilite_detaillee",
    )
    fuseau = models.CharField(max_length=64, default="Africa/Abidjan")
    modifie_le = models.DateTimeField(auto_now=True)


class CreneauHebdomadaire(models.Model):
    class Jour(models.IntegerChoices):
        LUNDI = 0, "Lundi"
        MARDI = 1, "Mardi"
        MERCREDI = 2, "Mercredi"
        JEUDI = 3, "Jeudi"
        VENDREDI = 4, "Vendredi"
        SAMEDI = 5, "Samedi"
        DIMANCHE = 6, "Dimanche"

    disponibilite = models.ForeignKey(
        DisponibiliteProfil,
        on_delete=models.CASCADE,
        related_name="creneaux",
    )
    jour = models.PositiveSmallIntegerField(choices=Jour.choices)
    debut = models.TimeField()
    fin = models.TimeField()

    class Meta:
        ordering = ("jour", "debut")
        constraints = [
            models.CheckConstraint(
                condition=Q(fin__gt=F("debut")),
                name="creneau_hebdomadaire_fin_apres_debut",
            )
        ]


class ExceptionDisponibilite(models.Model):
    disponibilite = models.ForeignKey(
        DisponibiliteProfil,
        on_delete=models.CASCADE,
        related_name="exceptions",
    )
    date = models.DateField()
    est_disponible = models.BooleanField(default=False)
    debut = models.TimeField(null=True, blank=True)
    fin = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ("date",)
        constraints = [
            models.UniqueConstraint(
                fields=("disponibilite", "date"),
                name="exception_disponibilite_unique_date",
            ),
            models.CheckConstraint(
                condition=(
                    Q(est_disponible=False, debut__isnull=True, fin__isnull=True)
                    | Q(
                        est_disponible=True,
                        debut__isnull=False,
                        fin__isnull=False,
                        fin__gt=F("debut"),
                    )
                ),
                name="exception_disponibilite_horaire_coherent",
            ),
        ]
