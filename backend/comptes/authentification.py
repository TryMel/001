import hashlib
import hmac
import time
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Utilisateur


class AuthentificationApiAkasha(JWTAuthentication):
    """Exclut les comptes staff de toutes les surfaces API publiques."""

    def get_user(self, validated_token):
        utilisateur = super().get_user(validated_token)
        if utilisateur.is_staff or utilisateur.is_superuser:
            raise AuthenticationFailed(
                "Ce compte est reserve a la console d'administration web.",
                code="compte_administration",
            )
        return utilisateur


def creer_jeton(utilisateur):
    expiration = int(time.time()) + 60 * 60 * 24 * 14
    charge = f"{utilisateur.pk}:{expiration}"
    signature = hmac.new(settings.SECRET_KEY.encode(), charge.encode(), hashlib.sha256).hexdigest()
    return f"{charge}:{signature}"


class AuthentificationJeton(BaseAuthentication):
    def authenticate(self, request):
        entete = request.headers.get("Authorization", "")
        if not entete.startswith("Bearer "):
            return None
        try:
            identifiant, expiration, signature = entete.removeprefix("Bearer ").split(":")
            charge = f"{identifiant}:{expiration}"
            attendu = hmac.new(settings.SECRET_KEY.encode(), charge.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, attendu) or int(expiration) < time.time():
                raise ValueError
            return Utilisateur.objects.get(pk=identifiant), None
        except (ValueError, Utilisateur.DoesNotExist):
            raise AuthenticationFailed("Jeton invalide ou expiré.")
