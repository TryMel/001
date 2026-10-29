from django.db import IntegrityError
from rest_framework import exceptions, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from .models import Utilisateur
from .serializers import (
    ConnexionSerializer,
    ConfirmationVerificationEmailSerializer,
    DemandeReinitialisationMotDePasseSerializer,
    InscriptionSerializer,
    ReinitialisationMotDePasseSerializer,
    RoleActifSerializer,
    RolesOnboardingSerializer,
    UtilisateurSerializer,
)
from .securite import (
    envoyer_lien_reinitialisation,
    envoyer_lien_verification,
    invalider_jetons_rafraichissement,
    utilisateur_depuis_lien,
    utilisateur_depuis_jeton_verification,
)


ReponseJetonsSerializer = inline_serializer(
    name="ReponseJetons",
    fields={
        "utilisateur": UtilisateurSerializer(),
        "access": serializers.CharField(),
        "refresh": serializers.CharField(),
    },
)


class InscriptionVue(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Identité"],
        request=InscriptionSerializer,
        responses={201: ReponseJetonsSerializer},
        description="Crée un compte, envoie un lien de vérification et retourne une paire JWT.",
    )
    def post(self, request):
        formulaire = InscriptionSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        try:
            utilisateur = formulaire.save()
        except IntegrityError as erreur:
            raise exceptions.ValidationError(
                {"email": "Un compte utilise déjà cette adresse."}
            ) from erreur
        envoyer_lien_verification(utilisateur)
        rafraichissement = RefreshToken.for_user(utilisateur)
        return Response({"utilisateur": UtilisateurSerializer(utilisateur).data, "access": str(rafraichissement.access_token), "refresh": str(rafraichissement)}, status=status.HTTP_201_CREATED)


class ConnexionVue(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ConnexionSerializer


class RafraichissementJetonVue(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class DeconnexionVue(TokenBlacklistView):
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    get=extend_schema(tags=["Identité"], responses=UtilisateurSerializer),
    patch=extend_schema(tags=["Identité"], request=UtilisateurSerializer, responses=UtilisateurSerializer),
)
class MonCompteVue(APIView):
    def get(self, request):
        return Response(UtilisateurSerializer(request.user).data)

    def patch(self, request):
        formulaire = UtilisateurSerializer(request.user, data=request.data, partial=True)
        formulaire.is_valid(raise_exception=True)
        formulaire.save()
        return Response(formulaire.data)


class TerminerOnboardingVue(APIView):
    @extend_schema(tags=["Identité"], request=RolesOnboardingSerializer, responses=UtilisateurSerializer)
    def post(self, request):
        formulaire = RolesOnboardingSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        utilisateur = request.user
        utilisateur.roles_professionnels = formulaire.validated_data[
            "roles_professionnels"
        ]
        utilisateur.role_actif = formulaire.validated_data["role_actif"]
        utilisateur.onboarding_termine = True
        utilisateur.save(
            update_fields=(
                "roles_professionnels",
                "role_actif",
                "onboarding_termine",
            )
        )
        return Response(UtilisateurSerializer(utilisateur).data)


class RoleActifVue(APIView):
    @extend_schema(tags=["Identité"], request=RoleActifSerializer, responses=UtilisateurSerializer)
    def patch(self, request):
        formulaire = RoleActifSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        utilisateur = request.user
        role = formulaire.validated_data["role_actif"]
        if role not in utilisateur.roles_professionnels:
            return Response(
                {
                    "code": "role_non_attribue",
                    "detail": "Vous ne disposez pas de cet espace.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        utilisateur.role_actif = role
        utilisateur.save(update_fields=("role_actif",))
        return Response(UtilisateurSerializer(utilisateur).data)


class DemandeReinitialisationMotDePasseVue(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [throttling.ScopedRateThrottle]
    throttle_scope = "reinitialisation_mot_de_passe"

    @extend_schema(
        tags=["Sécurité"],
        request=DemandeReinitialisationMotDePasseSerializer,
        responses={204: None},
        description="Déclenche un e-mail de récupération sans révéler si l’adresse existe.",
    )
    def post(self, request):
        formulaire = DemandeReinitialisationMotDePasseSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        utilisateur = (
            Utilisateur.objects.filter(
                email__iexact=formulaire.validated_data["email"],
                is_active=True,
            )
            .first()
        )
        if utilisateur:
            envoyer_lien_reinitialisation(utilisateur)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReinitialisationMotDePasseVue(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Sécurité"], request=ReinitialisationMotDePasseSerializer, responses={204: None})
    def post(self, request):
        formulaire = ReinitialisationMotDePasseSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        utilisateur = utilisateur_depuis_lien(
            formulaire.validated_data["uid"],
            formulaire.validated_data["token"],
        )
        if not utilisateur:
            raise exceptions.ValidationError(
                {"token": "Ce lien de réinitialisation est invalide ou expiré."}
            )
        utilisateur.set_password(formulaire.validated_data["mot_de_passe"])
        utilisateur.save(update_fields=("password",))
        invalider_jetons_rafraichissement(utilisateur)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EnvoiVerificationEmailVue(APIView):
    @extend_schema(tags=["Sécurité"], request=None, responses={204: None})
    def post(self, request):
        if not request.user.est_verifie:
            envoyer_lien_verification(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfirmationVerificationEmailVue(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Sécurité"], request=ConfirmationVerificationEmailSerializer, responses={204: None})
    def post(self, request):
        formulaire = ConfirmationVerificationEmailSerializer(data=request.data)
        formulaire.is_valid(raise_exception=True)
        utilisateur = utilisateur_depuis_jeton_verification(formulaire.validated_data["token"])
        if not utilisateur:
            raise exceptions.ValidationError({"token": "Ce lien de vérification est invalide ou expiré."})
        if not utilisateur.est_verifie:
            utilisateur.est_verifie = True
            utilisateur.save(update_fields=("est_verifie",))
        return Response(status=status.HTTP_204_NO_CONTENT)
