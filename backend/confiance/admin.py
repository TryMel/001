from django.contrib import admin

from .models import Evaluation, Signalement, Verification


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("evalue", "auteur", "collaboration", "note", "statut", "cree_le")
    list_filter = ("statut", "note", "cree_le")
    search_fields = ("evalue__email", "auteur__email", "collaboration__demande__titre")
    autocomplete_fields = ("evalue", "auteur", "collaboration")
    readonly_fields = ("cree_le",)
    date_hierarchy = "cree_le"


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "type", "statut", "cree_le")
    list_filter = ("type", "statut", "cree_le")
    search_fields = ("utilisateur__email", "reference_document")
    autocomplete_fields = ("utilisateur",)
    readonly_fields = ("cree_le",)
    date_hierarchy = "cree_le"
    fieldsets = (
        ("Demande", {"fields": ("utilisateur", "type", "reference_document")} ),
        ("Décision", {"fields": ("statut", "commentaire")} ),
        ("Traçabilité", {"fields": ("cree_le",)}),
    )


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ("motif", "statut", "auteur", "cible", "evaluation", "cree_le")
    list_filter = ("motif", "statut", "cree_le")
    search_fields = ("description", "auteur__email", "cible__email")
    autocomplete_fields = ("auteur", "cible", "evaluation")
    readonly_fields = ("cree_le",)
    date_hierarchy = "cree_le"
