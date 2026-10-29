from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import F, Q

from referentiel.models import Competence


class OffreService(models.Model):
    class Tarification(models.TextChoices):
        FORFAIT = "forfait", "Forfait"
        SUR_DEVIS = "sur_devis", "Sur devis"

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        PUBLIEE = "publiee", "Publiée"
        FERMEE = "fermee", "Fermée"

    profil = models.ForeignKey(
        "profils.ProfilProfessionnel",
        on_delete=models.CASCADE,
        related_name="offres_services",
    )
    titre = models.CharField(max_length=180)
    description = models.TextField()
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=2, default="CI")
    photo = models.ImageField(upload_to="services/", null=True, blank=True)
    images = GenericRelation(
        "medias.ImageContenu",
        content_type_field="type_contenu",
        object_id_field="contenu_id",
        related_query_name="offre_service",
    )
    tarification = models.CharField(
        max_length=12,
        choices=Tarification.choices,
        default=Tarification.SUR_DEVIS,
    )
    prix = models.PositiveIntegerField(null=True, blank=True)
    devise = models.CharField(max_length=3, default="XOF")
    delai_jours = models.PositiveSmallIntegerField(null=True, blank=True)
    statut = models.CharField(
        max_length=12,
        choices=Statut.choices,
        default=Statut.BROUILLON,
    )
    competences = models.ManyToManyField(Competence, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-cree_le",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(tarification="sur_devis", prix__isnull=True)
                    | Q(tarification="forfait", prix__isnull=False)
                ),
                name="offre_service_prix_coherent",
            )
        ]


class DemandeService(models.Model):
    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        OUVERTE = "ouverte", "Ouverte"
        EN_DISCUSSION = "en_discussion", "En discussion"
        ATTRIBUEE = "attribuee", "Attribuée"
        FERMEE = "fermee", "Fermée"
        EXPIREE = "expiree", "Expirée"

    class Visibilite(models.TextChoices):
        PUBLIQUE = "publique", "Publique"
        PRIVEE = "privee", "Privée"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="demandes_services",
    )
    organisation = models.ForeignKey(
        "organisations.Organisation",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="demandes_services",
    )
    titre = models.CharField(max_length=180)
    description = models.TextField()
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=2, default="CI")
    photo = models.ImageField(upload_to="demandes-services/", null=True, blank=True)
    images = GenericRelation(
        "medias.ImageContenu",
        content_type_field="type_contenu",
        object_id_field="contenu_id",
        related_query_name="demande_service",
    )
    budget_minimum = models.PositiveIntegerField(null=True, blank=True)
    budget_maximum = models.PositiveIntegerField(null=True, blank=True)
    devise = models.CharField(max_length=3, default="XOF")
    visibilite = models.CharField(
        max_length=12,
        choices=Visibilite.choices,
        default=Visibilite.PUBLIQUE,
    )
    statut = models.CharField(
        max_length=16,
        choices=Statut.choices,
        default=Statut.BROUILLON,
    )
    competences = models.ManyToManyField(Competence, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    publie_le = models.DateTimeField(null=True, blank=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-cree_le",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(budget_minimum__isnull=True)
                    | Q(budget_maximum__isnull=True)
                    | Q(budget_minimum__lte=F("budget_maximum"))
                ),
                name="demande_service_budget_minimum_lte_maximum",
            )
        ]


class Proposition(models.Model):
    class Statut(models.TextChoices):
        SOUMISE = "soumise", "Soumise"
        ACCEPTEE = "acceptee", "Acceptée"
        RETIREE = "retiree", "Retirée"
        REFUSEE = "refusee", "Refusée"

    demande = models.ForeignKey(
        DemandeService,
        on_delete=models.PROTECT,
        related_name="propositions",
    )
    prestataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="propositions_services",
    )
    montant = models.PositiveIntegerField()
    devise = models.CharField(max_length=3, default="XOF")
    delai_jours = models.PositiveSmallIntegerField()
    message = models.TextField(max_length=2000)
    statut = models.CharField(
        max_length=12,
        choices=Statut.choices,
        default=Statut.SOUMISE,
    )
    version = models.PositiveIntegerField(default=1)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-cree_le",)
        constraints = [
            models.UniqueConstraint(
                fields=("demande", "prestataire"),
                condition=Q(statut__in=("soumise", "acceptee")),
                name="proposition_active_unique_demande_prestataire",
            )
        ]


class Collaboration(models.Model):
    class Statut(models.TextChoices):
        ACCORDEE = "accordee", "Accordée"
        EN_COURS = "en_cours", "En cours"
        TERMINEE = "terminee", "Terminée"

    demande = models.ForeignKey(
        DemandeService,
        on_delete=models.PROTECT,
        related_name="collaborations",
    )
    proposition = models.OneToOneField(
        Proposition,
        on_delete=models.PROTECT,
        related_name="collaboration",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="collaborations_client",
    )
    prestataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="collaborations_prestataire",
    )
    perimetre = models.TextField()
    montant = models.PositiveIntegerField()
    devise = models.CharField(max_length=3, default="XOF")
    statut = models.CharField(
        max_length=16,
        choices=Statut.choices,
        default=Statut.ACCORDEE,
    )
    client_a_confirme_fin = models.BooleanField(default=False)
    prestataire_a_confirme_fin = models.BooleanField(default=False)
    debut = models.DateField(null=True, blank=True)
    echeance = models.DateField(null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    terminee_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-cree_le", "-pk")


class Jalon(models.Model):
    class Statut(models.TextChoices):
        A_FAIRE = "a_faire", "À faire"
        EN_COURS = "en_cours", "En cours"
        VALIDE = "valide", "Validé"

    collaboration = models.ForeignKey(
        Collaboration,
        on_delete=models.CASCADE,
        related_name="jalons",
    )
    titre = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=16,
        choices=Statut.choices,
        default=Statut.A_FAIRE,
    )
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("ordre", "id")


class Livrable(models.Model):
    jalon = models.ForeignKey(
        Jalon,
        on_delete=models.CASCADE,
        related_name="livrables",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    titre = models.CharField(max_length=180)
    lien = models.URLField(blank=True)
    commentaire = models.TextField(blank=True)
    est_valide = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
