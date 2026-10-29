from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CreneauHebdomadaire,
    DisponibiliteProfil,
    ExceptionDisponibilite,
    NiveauCompetence,
    ProfilProfessionnel,
)


class NiveauCompetenceInline(admin.TabularInline):
    model = NiveauCompetence
    extra = 0
    autocomplete_fields = ("competence",)


class CreneauHebdomadaireInline(admin.TabularInline):
    model = CreneauHebdomadaire
    extra = 0


class ExceptionDisponibiliteInline(admin.TabularInline):
    model = ExceptionDisponibilite
    extra = 0


@admin.register(ProfilProfessionnel)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "titre", "metier", "ville", "disponible", "visible_publiquement")
    list_filter = ("disponible", "visible_publiquement", "metier")
    search_fields = ("utilisateur__email", "utilisateur__first_name", "utilisateur__last_name", "titre", "ville")
    autocomplete_fields = ("utilisateur", "metier")
    readonly_fields = ("apercu_photo",)
    inlines = (NiveauCompetenceInline,)
    fieldsets = (
        ("Identite professionnelle", {"fields": ("utilisateur", "titre", "metier", "ville")} ),
        ("Presentation", {"fields": ("photo", "apercu_photo", "biographie")} ),
        ("Visibilite", {"fields": ("disponible", "visible_publiquement")} ),
    )

    @admin.display(description="Photo")
    def apercu_photo(self, obj):
        if not obj.photo:
            return "Aucune photo"
        return format_html('<img src="{}" style="height: 56px; width: 56px; border-radius: 14px; object-fit: cover;" />', obj.photo.url)


@admin.register(DisponibiliteProfil)
class DisponibiliteProfilAdmin(admin.ModelAdmin):
    list_display = ("profil", "fuseau", "modifie_le")
    search_fields = ("profil__utilisateur__email", "profil__titre")
    autocomplete_fields = ("profil",)
    readonly_fields = ("modifie_le",)
    inlines = (CreneauHebdomadaireInline, ExceptionDisponibiliteInline)


@admin.register(CreneauHebdomadaire)
class CreneauHebdomadaireAdmin(admin.ModelAdmin):
    list_display = ("disponibilite", "jour", "debut", "fin")
    list_filter = ("jour",)
    autocomplete_fields = ("disponibilite",)


@admin.register(ExceptionDisponibilite)
class ExceptionDisponibiliteAdmin(admin.ModelAdmin):
    list_display = ("disponibilite", "date", "est_disponible", "debut", "fin")
    list_filter = ("est_disponible", "date")
    autocomplete_fields = ("disponibilite",)
