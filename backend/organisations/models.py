from django.conf import settings
from django.db import models
from internationalisation.models import EntrepriseReference

class Organisation(models.Model):
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="organisations/logos/", null=True, blank=True)
    pays = models.CharField(max_length=2, default="CI")
    ville = models.CharField(max_length=100, blank=True)
    site_web = models.URLField(blank=True)
    reference_entreprise = models.ForeignKey(
        EntrepriseReference,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organisations_inscrites",
    )
    est_verifiee = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.nom

class AppartenanceOrganisation(models.Model):
    class Role(models.TextChoices): PROPRIETAIRE = "proprietaire", "Propriétaire"; RECRUTEUR = "recruteur", "Recruteur"; GESTIONNAIRE = "gestionnaire", "Gestionnaire"; MEMBRE = "membre", "Membre"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="membres")
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organisations")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBRE)
    class Meta: unique_together = ("organisation", "utilisateur")
