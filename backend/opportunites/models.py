from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from referentiel.models import Competence, Metier


class Opportunite(models.Model):
    class Type(models.TextChoices):
        EMPLOI = "emploi", "Emploi"
        MISSION = "mission", "Mission"
        STAGE = "stage", "Stage"

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        PUBLIEE = "publiee", "Publiée"
        FERMEE = "fermee", "Fermée"

    class Contrat(models.TextChoices):
        CDI = "cdi", "CDI"
        CDD = "cdd", "CDD"
        INTERIM = "interim", "Intérim"
        ALTERNANCE = "alternance", "Alternance"
        AUTRE = "autre", "Autre"

    class Urgence(models.TextChoices):
        NORMALE = "normale", "Normale"
        URGENTE = "urgente", "Urgente"

    createur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="opportunites",
    )
    organisation = models.ForeignKey(
        "organisations.Organisation",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="opportunites",
    )
    titre = models.CharField(max_length=180)
    description = models.TextField()
    type = models.CharField(max_length=12, choices=Type.choices)
    statut = models.CharField(
        max_length=12,
        choices=Statut.choices,
        default=Statut.BROUILLON,
    )
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=2, default="CI")
    budget_minimum = models.PositiveIntegerField(null=True, blank=True)
    budget_maximum = models.PositiveIntegerField(null=True, blank=True)
    devise = models.CharField(max_length=3, default="XOF")
    contrat = models.CharField(max_length=12, choices=Contrat.choices, blank=True)
    niveau_etudes = models.CharField(max_length=120, blank=True)
    duree = models.CharField(max_length=120, blank=True)
    livrables = models.TextField(blank=True)
    urgence = models.CharField(
        max_length=8,
        choices=Urgence.choices,
        default=Urgence.NORMALE,
    )
    motif_urgence = models.CharField(max_length=500, blank=True)
    date_limite_candidature = models.DateField(null=True, blank=True)
    metier = models.ForeignKey(Metier, null=True, blank=True, on_delete=models.SET_NULL)
    competences = models.ManyToManyField(Competence, blank=True)
    images = GenericRelation(
        "medias.ImageContenu",
        content_type_field="type_contenu",
        object_id_field="contenu_id",
        related_query_name="opportunite",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cree_le"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(budget_minimum__isnull=True)
                    | Q(budget_maximum__isnull=True)
                    | Q(budget_minimum__lte=models.F("budget_maximum"))
                ),
                name="opportunite_budget_minimum_lte_maximum",
            )
        ]


class Candidature(models.Model):
    class Statut(models.TextChoices):
        ENVOYEE = "envoyee", "Envoyée"
        EN_COURS = "en_cours", "En cours"
        RETENUE = "retenue", "Présélectionnée"
        ENTRETIEN = "entretien", "Entretien"
        OFFRE = "offre", "Offre"
        ACCEPTEE = "acceptee", "Acceptée"
        REFUSEE = "refusee", "Refusée"
        RETIREE = "retiree", "Retirée"

    opportunite = models.ForeignKey(
        Opportunite,
        on_delete=models.CASCADE,
        related_name="candidatures",
    )
    candidat = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(max_length=2000)
    profil_partage_snapshot = models.JSONField(default=dict, blank=True)
    partage_profil_consenti_le = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(
        max_length=12,
        choices=Statut.choices,
        default=Statut.ENVOYEE,
    )
    version = models.PositiveIntegerField(default=1)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cree_le"]
        constraints = [
            models.UniqueConstraint(
                fields=("opportunite", "candidat"),
                name="candidature_unique_opportunite_candidat",
            )
        ]


class HistoriqueCandidature(models.Model):
    candidature = models.ForeignKey(
        Candidature,
        on_delete=models.CASCADE,
        related_name="historique",
    )
    acteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    statut_precedent = models.CharField(max_length=12, blank=True)
    nouveau_statut = models.CharField(max_length=12, choices=Candidature.Statut.choices)
    motif = models.CharField(max_length=500, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["cree_le", "pk"]
