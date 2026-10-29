from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("auteur", "contenu", "lu_le", "cree_le")
    readonly_fields = ("auteur", "contenu", "lu_le", "cree_le")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "candidature", "liste_participants", "cree_le")
    search_fields = ("candidature__opportunite__titre", "participants__email")
    autocomplete_fields = ("candidature",)
    filter_horizontal = ("participants",)
    readonly_fields = ("cree_le",)
    inlines = (MessageInline,)

    @admin.display(description="Participants")
    def liste_participants(self, obj):
        return ", ".join(obj.participants.values_list("email", flat=True)[:3])


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "auteur", "extrait", "lu_le", "cree_le")
    list_filter = ("lu_le", "cree_le")
    search_fields = ("contenu", "auteur__email", "conversation__candidature__opportunite__titre")
    autocomplete_fields = ("conversation", "auteur")
    readonly_fields = ("client_message_id", "cree_le")
    date_hierarchy = "cree_le"

    @admin.display(description="Message")
    def extrait(self, obj):
        return obj.contenu[:72] + ("…" if len(obj.contenu) > 72 else "")
