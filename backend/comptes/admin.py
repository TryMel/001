from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Gestion lisible des identites sans exposer les donnees sensibles."""

    list_display = (
        "email",
        "nom_complet",
        "role_actif",
        "est_verifie",
        "onboarding_termine",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "role_actif",
        "est_verifie",
        "onboarding_termine",
        "is_staff",
        "is_active",
        "pays",
    )
    search_fields = ("email", "first_name", "last_name", "telephone")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "consentement_conditions_le")
    fieldsets = (
        ("Identite", {"fields": ("email", "password", "first_name", "last_name", "telephone", "pays")} ),
        ("Parcours Akasha", {"fields": ("roles_professionnels", "role_actif", "onboarding_termine", "est_verifie")} ),
        ("Consentement", {"fields": ("consentement_conditions_version", "consentement_conditions_le")} ),
        ("Acces administration", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Tracabilite", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = (
        ("Creer un compte", {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "telephone", "pays", "password1", "password2", "is_active", "is_staff")} ),
    )
    filter_horizontal = ("groups", "user_permissions")

    @admin.display(description="Nom")
    def nom_complet(self, obj):
        return obj.get_full_name() or "—"
