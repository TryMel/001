from django.conf import settings
from django.db import models
from django.db.models import Q


class Abonnement(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abonnements",
    )
    formule = models.CharField(max_length=80)
    debut = models.DateField()
    fin = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)


class Facture(models.Model):
    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EMISE = "emise", "Émise"
        PAYEE = "payee", "Payée"
        ANNULEE = "annulee", "Annulée"

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="factures",
    )
    reference = models.CharField(max_length=40, unique=True)
    montant = models.PositiveIntegerField()
    devise = models.CharField(max_length=3, default="XOF")
    statut = models.CharField(
        max_length=12,
        choices=Statut.choices,
        default=Statut.BROUILLON,
    )
    cree_le = models.DateTimeField(auto_now_add=True)


class RegleCommission(models.Model):
    version = models.PositiveIntegerField(unique=True)
    taux_pourcentage = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="regles_commission_creees",
    )
    effective_le = models.DateTimeField(null=True, blank=True)
    activee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="regles_commission_activees",
    )

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.CheckConstraint(
                condition=Q(taux_pourcentage__gte=0, taux_pourcentage__lte=100),
                name="facturation_commission_taux_valide",
            ),
            models.UniqueConstraint(
                fields=("active",),
                condition=Q(active=True),
                name="facturation_une_commission_active",
            ),
        ]

    def __str__(self):
        etat = "active" if self.active else "inactive"
        return f"Commission v{self.version} — {self.taux_pourcentage}% ({etat})"
