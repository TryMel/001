from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html

from medias.models import ImageContenu
from .models import Candidature, HistoriqueCandidature, Opportunite


class CandidatureInline(admin.TabularInline):
    model = Candidature
    extra = 0
    fields = ("candidat", "statut", "cree_le")
    readonly_fields = ("cree_le",)
    show_change_link = True


class ImageContenuInline(GenericTabularInline):
    """Galerie directement visible dans l'edition d'une opportunite."""

    model = ImageContenu
    ct_field = "type_contenu"
    ct_fk_field = "contenu_id"
    extra = 1
    max_num = 5
    fields = ("fichier", "position", "apercu")
    readonly_fields = ("apercu",)

    @admin.display(description="Apercu")
    def apercu(self, obj):
        if not obj or not obj.fichier:
            return "-"
        return format_html(
            '<img src="{}" alt="" style="max-width: 88px; max-height: 56px; border-radius: 6px;" />',
            obj.fichier.url,
        )


@admin.register(Opportunite)
class OpportuniteAdmin(admin.ModelAdmin):
    list_display = ("titre", "type", "statut", "createur", "organisation", "ville", "fourchette_budget", "cree_le")
    list_filter = ("statut", "type", "devise", "cree_le")
    search_fields = ("titre", "description", "ville", "createur__email", "createur__first_name", "createur__last_name")
    autocomplete_fields = ("createur", "organisation", "metier")
    filter_horizontal = ("competences",)
    readonly_fields = ("cree_le",)
    date_hierarchy = "cree_le"
    ordering = ("-cree_le",)
    inlines = (ImageContenuInline, CandidatureInline)
    fieldsets = (
        ("Publication", {"fields": (("titre", "type", "statut"), "description")} ),
        ("Responsable et localisation", {"fields": ("createur", "organisation", "metier", "competences", ("ville", "pays"))} ),
        ("Conditions et budget", {"fields": (("contrat", "duree"), "niveau_etudes", ("budget_minimum", "budget_maximum", "devise"), "livrables")} ),
        ("Calendrier", {"fields": (("date_limite_candidature", "urgence"), "motif_urgence")} ),
        ("Tracabilite", {"fields": ("cree_le",)}),
    )

    @admin.display(description="Budget")
    def fourchette_budget(self, obj):
        if obj.budget_minimum is None and obj.budget_maximum is None:
            return "Non precise"
        minimum = f"{obj.budget_minimum:,}" if obj.budget_minimum is not None else "—"
        maximum = f"{obj.budget_maximum:,}" if obj.budget_maximum is not None else "—"
        return f"{minimum} – {maximum} {obj.devise}"


class HistoriqueCandidatureInline(admin.TabularInline):
    model = HistoriqueCandidature
    extra = 0
    can_delete = False
    readonly_fields = ("acteur", "statut_precedent", "nouveau_statut", "motif", "cree_le")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ("opportunite", "candidat", "statut", "version", "cree_le")
    list_filter = ("statut", "cree_le")
    search_fields = ("opportunite__titre", "candidat__email", "candidat__first_name", "candidat__last_name")
    autocomplete_fields = ("opportunite", "candidat")
    readonly_fields = ("version", "cree_le")
    date_hierarchy = "cree_le"
    ordering = ("-cree_le",)
    inlines = (HistoriqueCandidatureInline,)
