from django.contrib import admin

from .models import Experience, Formation, Qualification, Realisation


class PortfolioAdminBase(admin.ModelAdmin):
    autocomplete_fields = ("profil",)
    search_fields = ("profil__utilisateur__email", "profil__titre")


@admin.register(Formation)
class FormationAdmin(PortfolioAdminBase):
    list_display = ("intitule", "etablissement", "profil", "debut", "fin", "est_verifiee")
    list_filter = ("est_verifiee", "debut")


@admin.register(Experience)
class ExperienceAdmin(PortfolioAdminBase):
    list_display = ("poste", "organisation", "profil", "debut", "fin", "est_attestee")
    list_filter = ("est_attestee", "debut")
    search_fields = PortfolioAdminBase.search_fields + ("poste", "organisation")


@admin.register(Realisation)
class RealisationAdmin(PortfolioAdminBase):
    list_display = ("titre", "profil", "date_realisation", "est_verifiee")
    list_filter = ("est_verifiee", "date_realisation")
    search_fields = PortfolioAdminBase.search_fields + ("titre", "description")


@admin.register(Qualification)
class QualificationAdmin(PortfolioAdminBase):
    list_display = ("nom", "organisme", "profil", "expiration", "est_confirmee")
    list_filter = ("est_confirmee", "expiration")
    search_fields = PortfolioAdminBase.search_fields + ("nom", "organisme", "reference")
