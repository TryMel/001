from django.db import models
from django.db.models import Q


class Metier(models.Model):
    code = models.CharField(max_length=24, unique=True)
    nom = models.CharField(max_length=150)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="specialites")
    classification_source = models.CharField(max_length=50, blank=True)
    code_source = models.CharField(max_length=100, blank=True)
    version_source = models.CharField(max_length=40, blank=True)
    url_source = models.URLField(blank=True)
    licence_source = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["nom"]
        constraints = [
            models.UniqueConstraint(
                fields=("classification_source", "code_source"),
                condition=Q(code_source__gt=""),
                name="metier_code_classification_unique",
            )
        ]

    def __str__(self): return self.nom


class Competence(models.Model):
    nom = models.CharField(max_length=150, unique=True)
    metiers = models.ManyToManyField(Metier, related_name="competences", blank=True)
    classification_source = models.CharField(max_length=50, blank=True)
    code_source = models.CharField(max_length=100, blank=True)
    version_source = models.CharField(max_length=40, blank=True)
    url_source = models.URLField(blank=True)
    licence_source = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["nom"]
        constraints = [
            models.UniqueConstraint(
                fields=("classification_source", "code_source"),
                condition=Q(code_source__gt=""),
                name="competence_code_classification_unique",
            )
        ]

    def __str__(self): return self.nom
