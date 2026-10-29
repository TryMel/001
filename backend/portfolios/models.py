from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from profils.models import ProfilProfessionnel
from internationalisation.models import EntrepriseReference

class Formation(models.Model):
    profil = models.ForeignKey(ProfilProfessionnel, on_delete=models.CASCADE, related_name="formations")
    etablissement = models.CharField(max_length=180); intitule = models.CharField(max_length=180)
    etablissement_reference = models.ForeignKey(
        "internationalisation.EtablissementReference",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="formations_de_profils",
    )
    programme_reference = models.ForeignKey(
        "internationalisation.ProgrammeFormationReference",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="formations_de_profils",
    )
    debut = models.DateField(); fin = models.DateField(null=True, blank=True); est_verifiee = models.BooleanField(default=False)
class Experience(models.Model):
    profil = models.ForeignKey(ProfilProfessionnel, on_delete=models.CASCADE, related_name="experiences")
    organisation = models.CharField(max_length=180); poste = models.CharField(max_length=180); description = models.TextField(blank=True)
    entreprise_reference = models.ForeignKey(
        EntrepriseReference,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="experiences",
    )
    debut = models.DateField(); fin = models.DateField(null=True, blank=True); est_attestee = models.BooleanField(default=False)
class Realisation(models.Model):
    profil = models.ForeignKey(ProfilProfessionnel, on_delete=models.CASCADE, related_name="realisations")
    titre = models.CharField(max_length=180); description = models.TextField(); lien = models.URLField(blank=True)
    images = GenericRelation(
        "medias.ImageContenu",
        content_type_field="type_contenu",
        object_id_field="contenu_id",
        related_query_name="realisation",
    )
    date_realisation = models.DateField(null=True, blank=True); est_verifiee = models.BooleanField(default=False)
class Qualification(models.Model):
    profil = models.ForeignKey(ProfilProfessionnel, on_delete=models.CASCADE, related_name="qualifications")
    nom = models.CharField(max_length=180); organisme = models.CharField(max_length=180); reference = models.CharField(max_length=100, blank=True)
    expiration = models.DateField(null=True, blank=True); est_confirmee = models.BooleanField(default=False)
