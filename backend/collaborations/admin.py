from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html

from medias.models import ImageContenu
from .models import Collaboration, DemandeService, Jalon, Livrable, OffreService, Proposition


class JalonInline(admin.TabularInline):
    model = Jalon
    extra = 0
    show_change_link = True


class PropositionInline(admin.TabularInline):
    model = Proposition
    extra = 0
    fields = ("prestataire", "montant", "devise", "delai_jours", "statut", "cree_le")
    readonly_fields = ("cree_le",)
    show_change_link = True


class ImageContenuInline(GenericTabularInline):
    model = ImageContenu
    ct_field = "type_contenu"
    ct_fk_field = "contenu_id"
    extra = 0
    max_num = 4
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


@admin.register(OffreService)
class OffreServiceAdmin(admin.ModelAdmin):
    list_display = ("titre", "profil", "tarification", "prix", "devise", "statut", "cree_le")
    list_filter = ("statut", "tarification", "devise")
    search_fields = ("titre", "description", "profil__utilisateur__email", "ville")
    autocomplete_fields = ("profil",)
    filter_horizontal = ("competences",)
    readonly_fields = ("cree_le", "modifie_le")
    date_hierarchy = "cree_le"
    ordering = ("-cree_le",)
    inlines = (ImageContenuInline,)
    fieldsets = (
        ("Service", {"fields": ("profil", ("titre", "statut"), "description")} ),
        ("Localisation et competences", {"fields": (("ville", "pays"), "competences")} ),
        ("Photo et facturation", {"fields": ("photo", ("tarification", "prix", "devise"), "delai_jours")} ),
        ("Tracabilite", {"fields": (("cree_le", "modifie_le"),)}),
    )


@admin.register(DemandeService)
class DemandeServiceAdmin(admin.ModelAdmin):
    list_display = ("titre", "client", "organisation", "statut", "visibilite", "ville", "cree_le")
    list_filter = ("statut", "visibilite", "devise", "cree_le")
    search_fields = ("titre", "description", "client__email", "organisation__nom", "ville")
    autocomplete_fields = ("client", "organisation")
    filter_horizontal = ("competences",)
    readonly_fields = ("cree_le", "publie_le", "modifie_le")
    date_hierarchy = "cree_le"
    ordering = ("-cree_le",)
    inlines = (ImageContenuInline, PropositionInline)
    fieldsets = (
        ("Demande", {"fields": (("client", "organisation"), ("titre", "statut", "visibilite"), "description")} ),
        ("Localisation et competences", {"fields": (("ville", "pays"), "competences")} ),
        ("Photo et budget", {"fields": ("photo", ("budget_minimum", "budget_maximum", "devise"))} ),
        ("Tracabilite", {"fields": (("cree_le", "publie_le", "modifie_le"),)}),
    )


@admin.register(Proposition)
class PropositionAdmin(admin.ModelAdmin):
    list_display = ("demande", "prestataire", "montant", "devise", "delai_jours", "statut", "cree_le")
    list_filter = ("statut", "devise", "cree_le")
    search_fields = ("demande__titre", "prestataire__email")
    autocomplete_fields = ("demande", "prestataire")
    readonly_fields = ("version", "cree_le", "modifie_le")
    ordering = ("-cree_le",)


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = ("demande", "client", "prestataire", "montant", "devise", "statut", "echeance")
    list_filter = ("statut", "devise")
    search_fields = ("demande__titre", "client__email", "prestataire__email")
    autocomplete_fields = ("demande", "proposition", "client", "prestataire")
    readonly_fields = ("cree_le", "terminee_le")
    inlines = (JalonInline,)


@admin.register(Jalon)
class JalonAdmin(admin.ModelAdmin):
    list_display = ("titre", "collaboration", "statut", "echeance", "ordre")
    list_filter = ("statut",)
    search_fields = ("titre", "collaboration__demande__titre")
    autocomplete_fields = ("collaboration",)
    ordering = ("collaboration", "ordre")


@admin.register(Livrable)
class LivrableAdmin(admin.ModelAdmin):
    list_display = ("titre", "jalon", "auteur", "est_valide", "cree_le")
    list_filter = ("est_valide", "cree_le")
    search_fields = ("titre", "jalon__titre", "auteur__email")
    autocomplete_fields = ("jalon", "auteur")
    readonly_fields = ("cree_le",)
