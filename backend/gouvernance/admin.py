from django.contrib import admin

from .models import JournalAudit


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ("cree_le", "acteur", "action", "cible")
    list_filter = ("action", "cree_le")
    search_fields = ("action", "cible", "acteur__email")
    autocomplete_fields = ("acteur",)
    readonly_fields = ("acteur", "action", "cible", "donnees", "cree_le")
    date_hierarchy = "cree_le"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
