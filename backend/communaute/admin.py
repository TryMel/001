from django.contrib import admin

from .models import Ressource


@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ("titre", "auteur", "metier", "publiee", "cree_le")
    list_filter = ("publiee", "metier", "cree_le")
    search_fields = ("titre", "contenu", "auteur__email")
    autocomplete_fields = ("auteur", "metier")
    readonly_fields = ("cree_le",)
    date_hierarchy = "cree_le"
