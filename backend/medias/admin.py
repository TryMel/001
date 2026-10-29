from django.contrib import admin
from django.utils.html import format_html

from .models import ImageContenu


@admin.register(ImageContenu)
class ImageContenuAdmin(admin.ModelAdmin):
    list_display = ("apercu", "type_contenu", "contenu_id", "position", "cree_le")
    list_filter = ("type_contenu", "cree_le")
    search_fields = ("fichier", "contenu_id")
    readonly_fields = ("apercu", "cree_le")
    ordering = ("-cree_le",)

    @admin.display(description="Aperçu")
    def apercu(self, obj):
        if not obj.fichier:
            return "Aucune image"
        return format_html(
            '<img src="{}" style="height: 48px; width: 48px; border-radius: 10px; object-fit: cover;" />',
            obj.fichier.url,
        )
