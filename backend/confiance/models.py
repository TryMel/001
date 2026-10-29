from django.conf import settings
from django.db import models


class Evaluation(models.Model):
    class Statut(models.TextChoices):
        PUBLIEE = "publiee", "Publiée"
        EN_REVISION = "en_revision", "En révision"
        RETIREE = "retiree", "Retirée"

    evalue = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evaluations_recues",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evaluations_ecrites",
    )
    collaboration = models.ForeignKey(
        "collaborations.Collaboration",
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    note = models.PositiveSmallIntegerField()
    commentaire = models.TextField(max_length=2000, blank=True)
    statut = models.CharField(
        max_length=12,
        choices=Statut.choices,
        default=Statut.PUBLIEE,
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-cree_le",)
        constraints = [
            models.UniqueConstraint(
                fields=("evalue", "auteur", "collaboration"),
                name="evaluation_unique_par_participant",
            )
        ]


class Verification(models.Model):
    class Type(models.TextChoices):
        IDENTITE = "identite", "Identité"
        QUALIFICATION = "qualification", "Qualification"
        EXPERIENCE = "experience", "Expérience"
        ORGANISATION = "organisation", "Organisation"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        CONFIRMEE = "confirmee", "Confirmée"
        REFUSEE = "refusee", "Refusée"

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    type = models.CharField(max_length=16, choices=Type.choices)
    statut = models.CharField(
        max_length=16,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )
    reference_document = models.CharField(max_length=255, blank=True)
    commentaire = models.TextField(blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)


class Signalement(models.Model):
    class Motif(models.TextChoices):
        FRAUDE = "fraude", "Fraude"
        ABUS = "abus", "Abus"
        CONTENU = "contenu", "Contenu inapproprié"
        AUTRE = "autre", "Autre"

    class Statut(models.TextChoices):
        OUVERT = "ouvert", "Ouvert"
        TRAITE = "traite", "Traité"
        REJETE = "rejete", "Rejeté"

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="signalements",
    )
    cible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="signalements_recus",
        null=True,
        blank=True,
    )
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.PROTECT,
        related_name="signalements",
        null=True,
        blank=True,
    )
    motif = models.CharField(max_length=16, choices=Motif.choices)
    description = models.TextField()
    statut = models.CharField(
        max_length=16,
        choices=Statut.choices,
        default=Statut.OUVERT,
    )
    cree_le = models.DateTimeField(auto_now_add=True)
