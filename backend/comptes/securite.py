from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core import signing
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import Utilisateur


def lien_reinitialisation(utilisateur: Utilisateur) -> str:
    identifiant = urlsafe_base64_encode(force_bytes(utilisateur.pk))
    jeton = default_token_generator.make_token(utilisateur)
    return f"{settings.AKASHA_MOBILE_SCHEME}://reinitialiser-mot-de-passe?uid={identifiant}&token={jeton}"


def envoyer_lien_reinitialisation(utilisateur: Utilisateur) -> None:
    lien = lien_reinitialisation(utilisateur)
    send_mail(
        subject="Réinitialisez votre mot de passe Akasha",
        message=(
            "Une demande de réinitialisation a été reçue pour votre compte Akasha.\n\n"
            f"Ouvrez ce lien dans l’application :\n{lien}\n\n"
            "Si vous n’êtes pas à l’origine de cette demande, aucune action n’est nécessaire."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[utilisateur.email],
        fail_silently=True,
    )


def envoyer_lien_verification(utilisateur: Utilisateur) -> None:
    jeton = signing.dumps({"utilisateur": utilisateur.pk}, salt="akasha.verification.email")
    lien = f"{settings.AKASHA_MOBILE_SCHEME}://verification?token={jeton}"
    send_mail(
        subject="Vérifiez votre adresse e-mail Akasha",
        message=(
            "Confirmez votre adresse e-mail pour sécuriser votre compte Akasha.\n\n"
            f"Ouvrez ce lien dans l’application :\n{lien}\n\n"
            "Si vous n’êtes pas à l’origine de cette demande, ignorez ce message."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[utilisateur.email],
        fail_silently=True,
    )


def utilisateur_depuis_jeton_verification(jeton: str) -> Utilisateur | None:
    try:
        charge = signing.loads(
            jeton,
            salt="akasha.verification.email",
            max_age=settings.AKASHA_VERIFICATION_MAX_AGE,
        )
        return Utilisateur.objects.get(pk=charge["utilisateur"])
    except (signing.BadSignature, signing.SignatureExpired, Utilisateur.DoesNotExist, KeyError, TypeError):
        return None


def utilisateur_depuis_lien(identifiant: str, jeton: str) -> Utilisateur | None:
    try:
        utilisateur = Utilisateur.objects.get(pk=force_str(urlsafe_base64_decode(identifiant)))
    except (Utilisateur.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
    if not default_token_generator.check_token(utilisateur, jeton):
        return None
    return utilisateur


def invalider_jetons_rafraichissement(utilisateur: Utilisateur) -> None:
    for jeton in OutstandingToken.objects.filter(user=utilisateur):
        BlacklistedToken.objects.get_or_create(token=jeton)
