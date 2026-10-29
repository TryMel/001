from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .admin_api import VueTableauBordAdministration

urlpatterns_api_v2 = [
    path(
        "api/v2/administration/overview/",
        VueTableauBordAdministration.as_view(api_version="v2"),
        name="administration-overview-v2",
    ),
    path("api/v2/comptes/", include("comptes.urls")),
    path("api/v2/referentiel/", include("referentiel.urls")),
    path("api/v2/profils/", include("profils.urls")),
    path("api/v2/opportunites/", include("opportunites.urls")),
    path("api/v2/collaborations/", include("collaborations.urls")),
    path("api/v2/messagerie/", include("messagerie.urls")),
    path("api/v2/organisations/", include("organisations.urls")),
    path("api/v2/portfolios/", include("portfolios.urls")),
    path("api/v2/confiance/", include("confiance.urls")),
    path("api/v2/notifications/", include("notifications.urls")),
    path("api/v2/facturation/", include("facturation.urls")),
    path("api/v2/internationalisation/", include("internationalisation.urls")),
    path("api/v2/communaute/", include("communaute.urls")),
    path("api/v2/analytique/", include("analytique.urls")),
    path("api/v2/correspondance/", include("correspondance.urls")),
]

urlpatterns = [
    re_path(r"^admin/(?P<reste>.*)$", RedirectView.as_view(url="/administration/%(reste)s", permanent=False)),
    path("administration/", admin.site.urls),
    path(
        "api/v1/administration/overview/",
        VueTableauBordAdministration.as_view(api_version="v1"),
        name="administration-overview-v1",
    ),
    path("api/comptes/", include("comptes.urls")),
    path("api/referentiel/", include("referentiel.urls")),
    path("api/profils/", include("profils.urls")),
    path("api/opportunites/", include("opportunites.urls")),
    path("api/collaborations/", include("collaborations.urls")),
    path("api/messagerie/", include("messagerie.urls")),
    path("api/organisations/", include("organisations.urls")),
    path("api/portfolios/", include("portfolios.urls")),
    path("api/confiance/", include("confiance.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/facturation/", include("facturation.urls")),
    path("api/internationalisation/", include("internationalisation.urls")),
    path("api/communaute/", include("communaute.urls")),
    path("api/analytique/", include("analytique.urls")),
    path("api/correspondance/", include("correspondance.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema-api"),
    path("api/documentation/", SpectacularSwaggerView.as_view(url_name="schema-api"), name="documentation-api"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema-api"), name="swagger-api"),
] + urlpatterns_api_v2 + [
    path(
        "api/v2/schema/",
        SpectacularAPIView.as_view(
            patterns=urlpatterns_api_v2,
            custom_settings={
                "TITLE": "API Akasha v2",
                "DESCRIPTION": "API v2 d’Akasha : endpoints versionnés sous /api/v2/.",
                "VERSION": "2.0.0",
            },
        ),
        name="schema-api-v2",
    ),
    path(
        "api/v2/documentation/",
        SpectacularSwaggerView.as_view(url_name="schema-api-v2"),
        name="documentation-api-v2",
    ),
    path(
        "api/v2/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema-api-v2"),
        name="swagger-api-v2",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
