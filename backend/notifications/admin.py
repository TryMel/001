from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("titre", "utilisateur", "est_lue", "cree_le")
    list_filter = ("lue_le", "cree_le")
    search_fields = ("titre", "message", "utilisateur__email")
    autocomplete_fields = ("utilisateur",)
    readonly_fields = ("cree_le", "lue_le")
    date_hierarchy = "cree_le"

    @admin.display(boolean=True, description="Lue")
    def est_lue(self, obj):
        return obj.lue_le is not None
