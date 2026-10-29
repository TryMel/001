from django.db import models


class EvenementInteraction(models.Model):
    class Fonctionnalite(models.TextChoices):
        ACCUEIL = "accueil", "Accueil"
        OPPORTUNITES = "opportunites", "Opportunités"
        CANDIDATURE = "candidature", "Candidature"
        PUBLICATION = "publication", "Publication"
        MESSAGERIE = "messagerie", "Messagerie"
        PROFIL = "profil", "Profil"
        SERVICES = "services", "Services"
        CHANGEMENT_ROLE = "changement_role", "Changement d’espace"
        ONBOARDING = "onboarding", "Choix des rôles"

    fonctionnalite = models.CharField(
        max_length=32,
        choices=Fonctionnalite.choices,
        db_index=True,
    )
    role_actif = models.CharField(max_length=24, db_index=True)
    cree_le = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-cree_le",)
        indexes = [
            models.Index(
                fields=("cree_le", "fonctionnalite", "role_actif"),
                name="an_event_date_fn_role_idx",
            )
        ]
        verbose_name = "clic suivi"
        verbose_name_plural = "clics suivis"

    def __str__(self):
        return f"{self.get_fonctionnalite_display()} — {self.role_actif} — {self.cree_le:%Y-%m-%d %H:%M}"
