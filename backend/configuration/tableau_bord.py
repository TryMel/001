import json
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from analytique.models import EvenementInteraction
from comptes.models import Utilisateur
from comptes.roles import ROLES_AKASHA
from collaborations.models import Collaboration, DemandeService
from confiance.models import Signalement, Verification
from facturation.models import Facture
from gouvernance.models import JournalAudit
from messagerie.models import Message
from opportunites.models import Candidature, Opportunite
from organisations.models import Organisation


ROLES = ROLES_AKASHA


def _borne_locale(jour):
    return timezone.make_aware(
        datetime.combine(jour, time.min),
        timezone.get_current_timezone(),
    )


def _serie_journaliere(queryset, champ_date, debut, fin):
    lignes = (
        queryset.filter(
            **{
                f"{champ_date}__gte": _borne_locale(debut),
                f"{champ_date}__lt": _borne_locale(fin + timedelta(days=1)),
            }
        )
        .annotate(
            jour=TruncDate(champ_date, tzinfo=timezone.get_current_timezone())
        )
        .values("jour")
        .annotate(total=Count("pk"))
    )
    valeurs = {ligne["jour"]: ligne["total"] for ligne in lignes}
    return [
        valeurs.get(debut + timedelta(days=offset), 0)
        for offset in range((fin - debut).days + 1)
    ]


def _options_graphique():
    return json.dumps(
        {
            "responsive": True,
            "maintainAspectRatio": False,
            "interaction": {"mode": "index", "intersect": False},
            "plugins": {
                "legend": {"position": "bottom"},
                "tooltip": {"enabled": True},
            },
            "scales": {
                "y": {"beginAtZero": True, "ticks": {"precision": 0}},
            },
        }
    )


def tableau_bord(request, context):
    maintenant = timezone.now()
    aujourd_hui = timezone.localdate(maintenant)
    debut = aujourd_hui - timedelta(days=29)
    actif_depuis = maintenant - timedelta(days=30)
    clics_recents = EvenementInteraction.objects.filter(cree_le__gte=actif_depuis)
    total_clics = clics_recents.count()
    fonctionnalites = list(EvenementInteraction.Fonctionnalite.choices)
    comptes_plateforme = Utilisateur.objects.filter(
        is_staff=False,
        is_superuser=False,
    )
    comptes_actifs = comptes_plateforme.filter(
        is_active=True,
        last_login__gte=actif_depuis,
    )

    matrice_clics = {
        fonctionnalite: {role: 0 for role, _ in ROLES}
        for fonctionnalite, _ in fonctionnalites
    }
    for ligne in (
        clics_recents.values("fonctionnalite", "role_actif")
        .annotate(total=Count("pk"))
        .order_by()
    ):
        valeurs_roles = matrice_clics.get(ligne["fonctionnalite"])
        if valeurs_roles is not None and ligne["role_actif"] in valeurs_roles:
            valeurs_roles[ligne["role_actif"]] = ligne["total"]

    analyse_fonctionnalites = [
        {
            "libelle": dict(fonctionnalites)[fonctionnalite],
            "roles": [
                {"libelle": libelle, "valeur": valeurs[role]}
                for role, libelle in ROLES
            ],
            "total": sum(valeurs.values()),
        }
        for fonctionnalite, valeurs in matrice_clics.items()
    ]
    analyse_fonctionnalites.sort(key=lambda ligne: ligne["total"], reverse=True)

    actifs_par_role = dict(
        comptes_actifs.values("role_actif")
        .annotate(total=Count("pk"))
        .values_list("role_actif", "total")
    )
    labels = [
        (aujourd_hui - timedelta(days=offset)).strftime("%d/%m")
        for offset in range(29, -1, -1)
    ]
    serie_inscriptions = _serie_journaliere(
        comptes_plateforme, "date_joined", debut, aujourd_hui
    )
    serie_opportunites = _serie_journaliere(
        Opportunite.objects.filter(statut=Opportunite.Statut.PUBLIEE),
        "cree_le",
        debut,
        aujourd_hui,
    )
    serie_candidatures = _serie_journaliere(
        Candidature.objects, "cree_le", debut, aujourd_hui
    )

    graphique_activite = {
        "labels": labels,
        "datasets": [
            {
                "label": "Nouveaux comptes",
                "data": serie_inscriptions,
                "borderColor": "#693fc2",
                "backgroundColor": "rgba(105, 63, 194, 0.10)",
                "tension": 0.35,
                "fill": True,
            },
            {
                "label": "Offres créées, actuellement publiées",
                "data": serie_opportunites,
                "borderColor": "#16856a",
                "backgroundColor": "rgba(22, 133, 106, 0.08)",
                "tension": 0.35,
                "fill": False,
            },
            {
                "label": "Candidatures",
                "data": serie_candidatures,
                "borderColor": "#dc8a19",
                "backgroundColor": "rgba(220, 138, 25, 0.08)",
                "tension": 0.35,
                "fill": False,
            },
        ],
    }
    graphique_fonctionnalites = {
        "labels": [
            ligne["libelle"]
            for ligne in analyse_fonctionnalites
            if ligne["total"] > 0
        ],
        "datasets": [
            {
                "label": "Clics sur 30 jours",
                "data": [
                    ligne["total"]
                    for ligne in analyse_fonctionnalites
                    if ligne["total"] > 0
                ],
                "backgroundColor": "#693fc2",
                "borderRadius": 6,
            }
        ],
    }
    graphique_roles = {
        "labels": [libelle for _, libelle in ROLES],
        "datasets": [
            {
                "label": "Comptes connectés sur 30 jours",
                "data": [actifs_par_role.get(role, 0) for role, _ in ROLES],
                "backgroundColor": "#693fc2",
                "borderRadius": 6,
            }
        ],
    }

    context.update(
        {
            "analytics_retention_days": settings.ANALYTICS_RETENTION_DAYS,
            "periode_debut": debut,
            "mis_a_jour_le": timezone.localtime(maintenant),
            "roles_analytiques": [libelle for _, libelle in ROLES],
            "lignes_fonctionnalites": analyse_fonctionnalites,
            "indicateurs": [
                {
                    "libelle": "Utilisateurs actifs (30 j)",
                    "valeur": comptes_actifs.count(),
                    "detail": "Comptes actifs connectés au cours des 30 derniers jours",
                },
                {
                    "libelle": "Nouveaux comptes (30 j)",
                    "valeur": comptes_plateforme.filter(
                        date_joined__gte=actif_depuis
                    ).count(),
                    "detail": "Comptes créés au cours des 30 derniers jours",
                },
                {
                    "libelle": "Clics mesurés (30 j)",
                    "valeur": total_clics,
                    "detail": "Interactions enregistrées dans les fonctionnalités suivies",
                },
                {
                    "libelle": "Candidatures (30 j)",
                    "valeur": Candidature.objects.filter(
                        cree_le__gte=actif_depuis
                    ).count(),
                    "detail": "Candidatures envoyées au cours des 30 derniers jours",
                },
                {
                    "libelle": "Opportunités publiées",
                    "valeur": Opportunite.objects.filter(
                        statut=Opportunite.Statut.PUBLIEE
                    ).count(),
                    "detail": "Offres actuellement publiées",
                },
                {
                    "libelle": "Organisations",
                    "valeur": Organisation.objects.count(),
                    "detail": "Entreprises et partenaires enregistrés",
                },
                {
                    "libelle": "Demandes ouvertes",
                    "valeur": DemandeService.objects.filter(statut="ouverte").count(),
                    "detail": "Demandes en attente de traitement",
                },
                {
                    "libelle": "Collaborations en cours",
                    "valeur": Collaboration.objects.filter(statut="en_cours").count(),
                    "detail": "Prestations actuellement en cours",
                },
                {
                    "libelle": "Factures enregistrées",
                    "valeur": Facture.objects.count(),
                    "detail": "Nombre de factures, sans extrapoler le chiffre d’affaires",
                },
            ],
            "graphe_activite": json.dumps(graphique_activite),
            "graphe_fonctionnalites": json.dumps(graphique_fonctionnalites),
            "graphe_roles": json.dumps(graphique_roles),
            "total_clics_30_jours": total_clics,
            "options_graphiques": _options_graphique(),
            "alertes": [
                {
                    "libelle": "Vérifications de pièces en attente",
                    "valeur": Verification.objects.filter(statut="en_attente").count(),
                    "lien": "/administration/confiance/verification/",
                    "urgent": True,
                },
                {
                    "libelle": "Signalements ouverts",
                    "valeur": Signalement.objects.filter(statut="ouvert").count(),
                    "lien": "/administration/confiance/signalement/",
                    "urgent": True,
                },
                {
                    "libelle": "Actions sensibles enregistrées (audit)",
                    "valeur": JournalAudit.objects.count(),
                    "lien": "/administration/gouvernance/journalaudit/",
                    "urgent": False,
                },
            ],
        }
    )
    return context
