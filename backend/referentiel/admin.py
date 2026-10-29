from django.contrib import admin

from .models import Competence, Metier


@admin.register(Metier)
class MetierAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "parent", "nombre_competences")
    list_filter = ("parent",)
    search_fields = ("nom", "code")
    ordering = ("nom",)
    autocomplete_fields = ("parent",)

    @admin.display(description="Competences")
    def nombre_competences(self, obj):
        return obj.competences.count()


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ("nom", "metiers_associes")
    search_fields = ("nom", "metiers__nom")
    ordering = ("nom",)
    filter_horizontal = ("metiers",)

    @admin.display(description="Metiers")
    def metiers_associes(self, obj):
        return ", ".join(obj.metiers.values_list("nom", flat=True)[:3]) or "—"
