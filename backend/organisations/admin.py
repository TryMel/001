from django.contrib import admin

from .models import AppartenanceOrganisation, Organisation


class AppartenanceInline(admin.TabularInline):
    model = AppartenanceOrganisation
    extra = 0
    autocomplete_fields = ("utilisateur",)


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("nom", "ville", "pays", "est_verifiee", "nombre_membres", "cree_le")
    list_filter = ("est_verifiee", "pays", "cree_le")
    search_fields = (
        "nom",
        "ville",
        "site_web",
        "reference_entreprise__nom",
        "reference_entreprise__identifiant_registre",
    )
    autocomplete_fields = ("reference_entreprise",)
    readonly_fields = ("cree_le",)
    ordering = ("nom",)
    inlines = (AppartenanceInline,)
    fieldsets = (
        ("Identite", {"fields": ("nom", "description", "photo")} ),
        (
            "Presence",
            {
                "fields": (
                    "pays",
                    "ville",
                    "site_web",
                    "reference_entreprise",
                    "est_verifiee",
                )
            },
        ),
        ("Tracabilite", {"fields": ("cree_le",)}),
    )

    @admin.display(description="Membres")
    def nombre_membres(self, obj):
        return obj.membres.count()


@admin.register(AppartenanceOrganisation)
class AppartenanceOrganisationAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "organisation", "role")
    list_filter = ("role",)
    search_fields = ("utilisateur__email", "organisation__nom")
    autocomplete_fields = ("utilisateur", "organisation")
