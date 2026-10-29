from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    # Limite compatible avec les index uniques MySQL utf8mb4 anciens.
    email = models.EmailField(max_length=191, unique=True)
    telephone = models.CharField(max_length=32, blank=True)
    pays = models.CharField(max_length=2, default="CI")
    est_verifie = models.BooleanField(default=False)
    roles_professionnels = models.JSONField(default=list, blank=True)
    role_actif = models.CharField(max_length=24, blank=True)
    onboarding_termine = models.BooleanField(default=False)
    consentement_conditions_le = models.DateTimeField(null=True, blank=True)
    consentement_conditions_version = models.CharField(max_length=32, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
