from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class StatutVerificationReference(models.TextChoices):
    DECLAREE = "declaree", "Déclarée, non vérifiée"
    A_VERIFIER = "a_verifier", "Vérification en cours"
    SOURCE_LISTEE = "source_listee", "Trouvée dans une source"
    DOCUMENT_VERIFIE = "document_verifie", "Document examiné"
    REGISTRE_CONFIRME = "registre_confirme", "Confirmée par le registre"
    INTROUVABLE = "introuvable", "Non retrouvée dans la source"
    CONTESTEE = "contestee", "Information contestée"
    PERIMEE = "perimee", "Vérification à renouveler"


class ReferenceVerifiable(models.Model):
    statut_verification = models.CharField(
        max_length=20,
        choices=StatutVerificationReference.choices,
        default=StatutVerificationReference.DECLAREE,
    )
    identifiant_registre = models.CharField(max_length=120, blank=True)
    autorite_source = models.CharField(max_length=180, blank=True)
    source_verification = models.CharField(max_length=180, blank=True)
    url_source = models.URLField(blank=True)
    version_source = models.CharField(max_length=80, blank=True)
    licence_source = models.CharField(max_length=120, blank=True)
    methode_verification = models.CharField(max_length=32, blank=True)
    reference_preuve = models.CharField(max_length=180, blank=True)
    recuperee_le = models.DateTimeField(null=True, blank=True)
    validee_pour_le = models.DateField(null=True, blank=True)
    note_verification = models.TextField(blank=True)
    verifiee_le = models.DateTimeField(null=True, blank=True)
    verifiee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_verifiees",
    )

    class Meta:
        abstract = True


class Marche(models.Model):
    code_pays = models.CharField(max_length=2, unique=True)
    nom = models.CharField(max_length=100)
    devise = models.CharField(max_length=3)
    fuseau_horaire = models.CharField(max_length=64)
    langues = models.CharField(max_length=120, default="fr")
    est_actif = models.BooleanField(default=False)

    def __str__(self): return self.nom


class RegleMetierLocale(models.Model):
    marche = models.ForeignKey(Marche, on_delete=models.CASCADE, related_name="regles")
    cle = models.CharField(max_length=100)
    valeur = models.JSONField(default=dict)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("marche", "cle")


class Ville(models.Model):
    marche = models.ForeignKey(
        Marche,
        on_delete=models.CASCADE,
        related_name="villes",
    )
    nom = models.CharField(max_length=120)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="villes_ajoutees",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nom",)
        constraints = [
            models.UniqueConstraint(
                Lower("nom"),
                "marche",
                name="ville_nom_unique_par_pays",
            )
        ]

    def __str__(self):
        return f"{self.nom} ({self.marche.code_pays})"


class EntrepriseReference(ReferenceVerifiable):
    marche = models.ForeignKey(
        Marche,
        on_delete=models.CASCADE,
        related_name="entreprises",
    )
    nom = models.CharField(max_length=180)
    forme_juridique = models.CharField(max_length=100, blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entreprises_ajoutees",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nom",)
        constraints = [
            models.UniqueConstraint(
                Lower("nom"),
                "marche",
                name="entreprise_nom_unique_par_pays",
            )
        ]

    def __str__(self):
        return f"{self.nom} ({self.marche.code_pays})"


class EtablissementReference(ReferenceVerifiable):
    class Type(models.TextChoices):
        UNIVERSITE = "universite", "Université"
        ECOLE = "ecole", "École ou institut"
        CENTRE_FORMATION = "centre_formation", "Centre de formation"
        AUTRE = "autre", "Autre établissement"

    marche = models.ForeignKey(
        Marche,
        on_delete=models.CASCADE,
        related_name="etablissements",
    )
    nom = models.CharField(max_length=180)
    type = models.CharField(max_length=24, choices=Type.choices, default=Type.AUTRE)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="etablissements_ajoutes",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nom",)
        constraints = [
            models.UniqueConstraint(
                Lower("nom"),
                "marche",
                name="etablissement_nom_unique_par_pays",
            )
        ]

    def __str__(self):
        return f"{self.nom} ({self.marche.code_pays})"


class ProgrammeFormationReference(ReferenceVerifiable):
    marche = models.ForeignKey(
        Marche,
        on_delete=models.CASCADE,
        related_name="programmes_formation",
    )
    etablissement = models.ForeignKey(
        EtablissementReference,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="programmes",
    )
    intitule = models.CharField(max_length=180)
    niveau = models.CharField(max_length=100, blank=True)
    metiers = models.ManyToManyField(
        "referentiel.Metier",
        related_name="programmes_formation",
        blank=True,
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="programmes_formation_ajoutes",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("intitule",)
        constraints = [
            models.UniqueConstraint(
                Lower("intitule"),
                "marche",
                "etablissement",
                name="programme_nom_unique_par_etablissement",
            )
        ]

    def __str__(self):
        return self.intitule
