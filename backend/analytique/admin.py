from django.contrib import admin

from .models import EvenementInteraction


@admin.register(EvenementInteraction)
class EvenementInteractionAdmin(admin.ModelAdmin):
    date_hierarchy = "cree_le"
    list_display = ("fonctionnalite", "role_actif", "cree_le")
    list_filter = ("fonctionnalite", "role_actif", "cree_le")
    ordering = ("-cree_le",)
    readonly_fields = ("fonctionnalite", "role_actif", "cree_le")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(
            request,
            obj,
        )
