from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .models import Abonnement, Facture, RegleCommission

@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "formule", "debut", "fin", "actif")
    list_filter = ("actif", "formule", "debut")
    search_fields = ("utilisateur__email", "formule")
    autocomplete_fields = ("utilisateur",)


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ("reference", "utilisateur", "montant", "devise", "statut", "cree_le")
    list_filter = ("statut", "devise", "cree_le")
    search_fields = ("reference", "utilisateur__email")
    autocomplete_fields = ("utilisateur",)
    readonly_fields = ("cree_le",)
    date_hierarchy = "cree_le"


@admin.register(RegleCommission)
class RegleCommissionAdmin(admin.ModelAdmin):
    list_display = (
        "version",
        "taux_pourcentage",
        "active",
        "cree_le",
        "effective_le",
        "cree_par",
        "activee_par",
    )
    list_filter = ("active",)
    ordering = ("-version",)
    readonly_fields = (
        "version",
        "active",
        "cree_le",
        "cree_par",
        "effective_le",
        "activee_par",
    )
    actions = ("activer_regle",)

    def get_readonly_fields(self, request, obj=None):
        champs = super().get_readonly_fields(request, obj)
        return (*champs, "taux_pourcentage") if obj else champs

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            derniere_version = (
                RegleCommission.objects.order_by("-version")
                .values_list("version", flat=True)
                .first()
                or 0
            )
            obj.version = derniere_version + 1
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Activer la règle de commission sélectionnée")
    def activer_regle(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Sélectionnez exactement une règle à activer.",
                level=messages.ERROR,
            )
            return

        with transaction.atomic():
            regle = queryset.select_for_update().get()
            RegleCommission.objects.exclude(pk=regle.pk).filter(active=True).update(
                active=False
            )
            regle.active = True
            regle.effective_le = timezone.now()
            regle.activee_par = request.user
            regle.save(
                update_fields=("active", "effective_le", "activee_par")
            )
            self.log_change(
                request,
                regle,
                f"Activation de la règle de commission v{regle.version}.",
            )

        self.message_user(
            request,
            f"La règle v{regle.version} ({regle.taux_pourcentage} %) est active pour les nouvelles commandes.",
            level=messages.SUCCESS,
        )
