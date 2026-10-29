import os
from pathlib import Path
from datetime import timedelta
from collections.abc import Mapping
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

_CLE_SECRETE_DEVELOPPEMENT = "cle-developpement-a-remplacer-immediatement"


def _lire_configuration_securite(environnement: Mapping[str, str]) -> tuple[str, bool]:
    secret_key = environnement.get("SECRET_KEY", "").strip()
    if not secret_key or secret_key == _CLE_SECRETE_DEVELOPPEMENT:
        raise ImproperlyConfigured(
            "SECRET_KEY doit être défini avec une valeur propre à l'environnement."
        )
    debug = environnement.get("DEBUG", "False").lower() == "true"
    return secret_key, debug


SECRET_KEY, DEBUG = _lire_configuration_securite(os.environ)


def _split_csv(valeur: str | None, defaut: str = "") -> list[str]:
    if not valeur:
        return [item.strip() for item in defaut.split(",") if item.strip()]
    return [item.strip() for item in valeur.split(",") if item.strip()]


def _lire_booleen(nom: str, defaut: bool) -> bool:
    """Lit explicitement les drapeaux de sécurité sans casser le développement local."""
    valeur = os.getenv(nom)
    if valeur is None:
        return defaut
    return valeur.strip().lower() in {"1", "true", "yes", "on"}


ALLOWED_HOSTS = _split_csv(
    os.getenv("ALLOWED_HOSTS"),
    "localhost,127.0.0.1,.localhost,0.0.0.0,testserver",
)
CORS_ALLOWED_ORIGINS = _split_csv(
    os.getenv("CORS_ALLOWED_ORIGINS"),
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081,http://127.0.0.1:8081,http://localhost:8082,http://127.0.0.1:8082",
)
CORS_ALLOWED_ORIGIN_REGEXES = _split_csv(
    os.getenv("CORS_ALLOWED_ORIGIN_REGEXES"),
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$" if DEBUG else "",
)
CSRF_TRUSTED_ORIGINS = _split_csv(
    os.getenv("CSRF_TRUSTED_ORIGINS"),
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081,http://127.0.0.1:8081",
)
# Les valeurs sûres sont activées par défaut en production. Elles restent
# désactivées avec DEBUG=True afin de ne pas empêcher les serveurs HTTP locaux.
SECURE_SSL_REDIRECT = _lire_booleen("SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = _lire_booleen("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = _lire_booleen("CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = _lire_booleen(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG
)
SECURE_HSTS_PRELOAD = _lire_booleen("SECURE_HSTS_PRELOAD", False)

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "comptes",
    "referentiel",
    "profils",
    "opportunites",
    "collaborations",
    "messagerie",
    "organisations",
    "medias.apps.MediasConfig",
    "portfolios",
    "confiance",
    "notifications",
    "facturation",
    "internationalisation",
    "communaute",
    "gouvernance",
    "analytique",
    "correspondance",
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "configuration.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": [
    "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
]}}]
WSGI_APPLICATION = "configuration.wsgi.application"
DATABASE_ENGINE = os.getenv(
    "DATABASE_ENGINE",
    "django.db.backends.postgresql",
)
if DATABASE_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DATABASE_ENGINE,
            "NAME": os.getenv("SQLITE_DATABASE", ":memory:"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DATABASE_ENGINE,
            "NAME": os.getenv("POSTGRES_DATABASE", "akasha"),
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
AUTH_USER_MODEL = "comptes.Utilisateur"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "statique"]
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@akasha.local")
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
AKASHA_MOBILE_SCHEME = os.getenv("AKASHA_MOBILE_SCHEME", "akasha")
AKASHA_VERIFICATION_MAX_AGE = int(os.getenv("AKASHA_VERIFICATION_MAX_AGE", "86400"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 27 * 1024 * 1024
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOW_ALL_ORIGINS = False
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["comptes.authentification.AuthentificationApiAkasha"], "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination", "PAGE_SIZE": 20, "DEFAULT_FILTER_BACKENDS": ["rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"], "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema", "EXCEPTION_HANDLER": "configuration.exceptions.gestionnaire_exceptions", "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"], "DEFAULT_THROTTLE_RATES": {"anon": "30/minute", "user": "120/minute", "reinitialisation_mot_de_passe": "5/hour"}}
ANALYTICS_RETENTION_DAYS = int(os.getenv("ANALYTICS_RETENTION_DAYS", "365"))
if not 1 <= ANALYTICS_RETENTION_DAYS <= 365:
    raise ValueError("ANALYTICS_RETENTION_DAYS doit être compris entre 1 et 365.")
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), "REFRESH_TOKEN_LIFETIME": timedelta(days=14), "ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True, "UPDATE_LAST_LOGIN": True, "AUTH_HEADER_TYPES": ("Bearer",)}
SPECTACULAR_SETTINGS = {"TITLE": "API Akasha", "DESCRIPTION": "API de la plateforme professionnelle Akasha.", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False}
UNFOLD = {
    "SITE_TITLE": "Akasha Console",
    "SITE_HEADER": "AKASHA",
    "SITE_SUBHEADER": "Console des opérations",
    "SITE_URL": "/administration/",
    "SITE_LOGO": {"light": lambda request: static("akasha/logo-akasha.svg"), "dark": lambda request: static("akasha/logo-akasha.svg")},
    "SITE_ICON": {"light": lambda request: static("akasha/favicon.svg"), "dark": lambda request: static("akasha/favicon.svg")},
    "SITE_FAVICONS": [{"rel": "icon", "type": "image/svg+xml", "href": lambda request: static("akasha/favicon.svg")}],
    "DASHBOARD_CALLBACK": "configuration.tableau_bord.tableau_bord",
    "STYLES": [lambda request: static("akasha/admin.css")],
    "LOGIN": {"form": "comptes.forms.FormulaireConnexionAdministration"},
    "COLORS": {
        "primary": {"50": "#F5F0FF", "100": "#E8DDFF", "200": "#D2BFFF", "300": "#B38CFA", "400": "#8B5CF6", "500": "#6D3FC5", "600": "#5934A3", "700": "#492B85", "800": "#3B236C", "900": "#2D1A53", "950": "#1D1038"},
        "base": {"50": "#F8F8FB", "100": "#F0F1F6", "200": "#E1E4EC", "300": "#C7CBD6", "400": "#8B93A7", "500": "#667085", "600": "#475467", "700": "#344054", "800": "#1D2939", "900": "#101828", "950": "#090F1C"},
    },
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "navigation": [
            {
                "title": "Pilotage",
                "items": [
                    {"title": "Vue d’ensemble", "link": "/administration/", "icon": "dashboard"},
                    {"title": "Utilisateurs", "link": "/administration/comptes/utilisateur/", "icon": "group"},
                    {"title": "Profils professionnels", "link": "/administration/profils/profilprofessionnel/", "icon": "badge"},
                    {"title": "Organisations", "link": "/administration/organisations/organisation/", "icon": "corporate_fare"},
                    {"title": "Membres d’organisations", "link": "/administration/organisations/appartenanceorganisation/", "icon": "groups"},
                ],
            },
            {
                "title": "Marché et collaborations",
                "items": [
                    {"title": "Opportunités", "link": "/administration/opportunites/opportunite/", "icon": "work_outline"},
                    {"title": "Candidatures", "link": "/administration/opportunites/candidature/", "icon": "assignment"},
                    {"title": "Offres de service", "link": "/administration/collaborations/offreservice/", "icon": "storefront"},
                    {"title": "Demandes de service", "link": "/administration/collaborations/demandeservice/", "icon": "request_quote"},
                    {"title": "Propositions", "link": "/administration/collaborations/proposition/", "icon": "handshake"},
                    {"title": "Collaborations", "link": "/administration/collaborations/collaboration/", "icon": "diversity_3"},
                    {"title": "Jalons et livrables", "link": "/administration/collaborations/jalon/", "icon": "checklist"},
                ],
            },
            {
                "title": "Profils, contenus et communauté",
                "items": [
                    {"title": "Expériences", "link": "/administration/portfolios/experience/", "icon": "business_center"},
                    {"title": "Formations", "link": "/administration/portfolios/formation/", "icon": "school"},
                    {"title": "Réalisations", "link": "/administration/portfolios/realisation/", "icon": "collections"},
                    {"title": "Qualifications", "link": "/administration/portfolios/qualification/", "icon": "workspace_premium"},
                    {"title": "Disponibilités", "link": "/administration/profils/disponibiliteprofil/", "icon": "schedule"},
                    {"title": "Images de contenu", "link": "/administration/medias/imagecontenu/", "icon": "image"},
                    {"title": "Ressources", "link": "/administration/communaute/ressource/", "icon": "menu_book"},
                ],
            },
            {
                "title": "Confiance et sécurité",
                "items": [
                    {"title": "Évaluations", "link": "/administration/confiance/evaluation/", "icon": "star_rate"},
                    {"title": "Vérifications", "link": "/administration/confiance/verification/", "icon": "verified_user"},
                    {"title": "Signalements", "link": "/administration/confiance/signalement/", "icon": "report_problem"},
                    {"title": "Journal d’audit", "link": "/administration/gouvernance/journalaudit/", "icon": "history"},
                ],
            },
            {
                "title": "Communication et facturation",
                "items": [
                    {"title": "Conversations", "link": "/administration/messagerie/conversation/", "icon": "forum"},
                    {"title": "Messages", "link": "/administration/messagerie/message/", "icon": "chat"},
                    {"title": "Notifications", "link": "/administration/notifications/notification/", "icon": "notifications"},
                    {"title": "Abonnements", "link": "/administration/facturation/abonnement/", "icon": "subscriptions"},
                    {"title": "Factures", "link": "/administration/facturation/facture/", "icon": "receipt_long"},
                    {"title": "Règles de commission", "link": "/administration/facturation/reglecommission/", "icon": "percent"},
                ],
            },
            {
                "title": "Référentiels internationaux",
                "items": [
                    {"title": "Métiers", "link": "/administration/referentiel/metier/", "icon": "category"},
                    {"title": "Compétences", "link": "/administration/referentiel/competence/", "icon": "psychology"},
                    {"title": "Marchés et pays", "link": "/administration/internationalisation/marche/", "icon": "public"},
                    {"title": "Villes", "link": "/administration/internationalisation/ville/", "icon": "location_city"},
                    {"title": "Entreprises de référence", "link": "/administration/internationalisation/entreprisereference/", "icon": "apartment"},
                    {"title": "Établissements", "link": "/administration/internationalisation/etablissementreference/", "icon": "account_balance"},
                    {"title": "Programmes de formation", "link": "/administration/internationalisation/programmeformationreference/", "icon": "school"},
                    {"title": "Règles locales", "link": "/administration/internationalisation/reglemetierlocale/", "icon": "gavel"},
                ],
            },
            {
                "title": "Mesure et maintenance",
                "items": [
                    {"title": "Interactions agrégées", "link": "/administration/analytique/evenementinteraction/", "icon": "monitoring"},
                ],
            },
        ],
    },
}
