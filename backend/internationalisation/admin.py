from django.contrib import admin

from .models import (
    EntrepriseReference,
    EtablissementReference,
    Marche,
    ProgrammeFormationReference,
    RegleMetierLocale,
    Ville,
)


class RegleMetierLocaleInline(admin.TabularInline):
    model = RegleMetierLocale
    extra = 0


@admin.register(Marche)
class MarcheAdmin(admin.ModelAdmin):
    list_display = ("nom", "code_pays", "devise", "fuseau_horaire", "est_actif")
    list_filter = ("est_actif", "devise")
    search_fields = ("nom", "code_pays", "langues")
    ordering = ("nom",)
    inlines = (RegleMetierLocaleInline,)


@admin.register(RegleMetierLocale)
class RegleMetierLocaleAdmin(admin.ModelAdmin):
    list_display = ("cle", "marche", "active")
    list_filter = ("active", "marche")
    search_fields = ("cle", "marche__nom")
    autocomplete_fields = ("marche",)


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ("nom", "marche", "cree_par", "cree_le")
    list_filter = ("marche",)
    search_fields = ("nom", "marche__nom", "marche__code_pays")
    autocomplete_fields = ("marche", "cree_par")


@admin.register(EntrepriseReference)
class EntrepriseReferenceAdmin(admin.ModelAdmin):
    list_display = ("nom", "marche", "statut_verification", "cree_le")
    list_filter = ("marche", "statut_verification")
    search_fields = ("nom", "identifiant_registre", "marche__nom", "marche__code_pays")
    autocomplete_fields = ("marche", "cree_par", "verifiee_par")


@admin.register(EtablissementReference)
class EtablissementReferenceAdmin(admin.ModelAdmin):
    list_display = ("nom", "marche", "type", "statut_verification", "cree_le")
    list_filter = ("marche", "type", "statut_verification")
    search_fields = ("nom", "identifiant_registre", "marche__nom", "marche__code_pays")
    autocomplete_fields = ("marche", "cree_par", "verifiee_par")


@admin.register(ProgrammeFormationReference)
class ProgrammeFormationReferenceAdmin(admin.ModelAdmin):
    list_display = ("intitule", "etablissement", "marche", "statut_verification")
    list_filter = ("marche", "statut_verification")
    search_fields = ("intitule", "etablissement__nom", "identifiant_registre")
    autocomplete_fields = ("marche", "etablissement", "metiers", "cree_par", "verifiee_par")
