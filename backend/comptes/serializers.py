from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
import re

from .models import Utilisateur
from .roles import ROLES_FONCTIONNELS
VERSION_CONDITIONS = "1.0"


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "telephone",
            "pays",
            "est_verifie",
            "roles_professionnels",
            "role_actif",
            "onboarding_termine",
            "consentement_conditions_le",
            "consentement_conditions_version",
        )
        read_only_fields = (
            "id",
            "email",
            "username",
            "est_verifie",
            "roles_professionnels",
            "role_actif",
            "onboarding_termine",
            "consentement_conditions_le",
            "consentement_conditions_version",
        )

    def validate_first_name(self, valeur):
        return valeur.strip()

    def validate_last_name(self, valeur):
        return valeur.strip()

    def validate_telephone(self, valeur):
        valeur = valeur.strip()
        if not valeur:
            return valeur
        if not re.fullmatch(r"[+\d().\-\s]{6,32}", valeur):
            raise serializers.ValidationError("Saisissez un numéro de téléphone valide.")
        if valeur.startswith("+"):
            chiffres = re.sub(r"\D", "", valeur)
            if not re.fullmatch(r"[1-9]\d{6,14}", chiffres):
                raise serializers.ValidationError(
                    "Le numéro international doit contenir 7 à 15 chiffres."
                )
            return f"+{chiffres}"
        if sum(caractere.isdigit() for caractere in valeur) < 6:
            raise serializers.ValidationError(
                "Saisissez un numéro de téléphone valide (32 caractères maximum)."
            )
        return valeur

    def validate_pays(self, valeur):
        valeur = valeur.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", valeur):
            raise serializers.ValidationError(
                "Le pays doit être indiqué avec son code ISO à deux lettres."
            )
        return valeur


class InscriptionSerializer(UtilisateurSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    conditions_acceptees = serializers.BooleanField(write_only=True, required=True)

    class Meta(UtilisateurSerializer.Meta):
        fields = UtilisateurSerializer.Meta.fields + (
            "password",
            "conditions_acceptees",
        )

    def validate_email(self, email):
        email_normalise = email.strip().lower()
        if Utilisateur.objects.filter(email__iexact=email_normalise).exists():
            raise serializers.ValidationError("Un compte utilise déjà cette adresse.")
        return email_normalise

    def validate_password(self, valeur):
        utilisateur = Utilisateur(
            email=self.initial_data.get("email", ""),
            first_name=self.initial_data.get("first_name", ""),
            last_name=self.initial_data.get("last_name", ""),
        )
        validate_password(valeur, utilisateur)
        return valeur

    def validate_conditions_acceptees(self, accepte):
        if not accepte:
            raise serializers.ValidationError(
                "L'acceptation des conditions est requise pour créer un compte."
            )
        return accepte

    def create(self, donnees):
        donnees.pop("conditions_acceptees")
        mot_de_passe = donnees.pop("password")
        donnees.setdefault("username", donnees["email"])
        donnees["consentement_conditions_le"] = timezone.now()
        donnees["consentement_conditions_version"] = VERSION_CONDITIONS
        return Utilisateur.objects.create_user(password=mot_de_passe, **donnees)


class ConnexionSerializer(TokenObtainPairSerializer):
    def validate(self, donnees):
        champ_identifiant = self.username_field
        if isinstance(donnees.get(champ_identifiant), str):
            donnees[champ_identifiant] = donnees[champ_identifiant].strip().lower()
        jetons = super().validate(donnees)
        if self.user.is_staff or self.user.is_superuser:
            raise serializers.ValidationError(
                {
                    "email": (
                        "Ce compte est reserve a la console d'administration web. "
                        "Utilisez un compte Akasha non administrateur dans l'application."
                    )
                }
            )
        jetons["utilisateur"] = UtilisateurSerializer(self.user).data
        return jetons


class RolesOnboardingSerializer(serializers.Serializer):
    roles_professionnels = serializers.ListField(
        child=serializers.ChoiceField(choices=ROLES_FONCTIONNELS),
        allow_empty=False,
    )
    role_actif = serializers.ChoiceField(choices=ROLES_FONCTIONNELS)

    def validate(self, donnees):
        roles = donnees["roles_professionnels"]
        if len(roles) != len(set(roles)):
            raise serializers.ValidationError(
                {"roles_professionnels": "Un rôle ne peut apparaître qu'une fois."}
            )
        if donnees["role_actif"] not in roles:
            raise serializers.ValidationError(
                {"role_actif": "L'espace actif doit faire partie des rôles sélectionnés."}
            )
        return donnees


class RoleActifSerializer(serializers.Serializer):
    role_actif = serializers.ChoiceField(choices=ROLES_FONCTIONNELS)


class DemandeReinitialisationMotDePasseSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, valeur):
        return valeur.strip().lower()


class ReinitialisationMotDePasseSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=256)
    mot_de_passe = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    def validate_mot_de_passe(self, valeur):
        validate_password(valeur)
        return valeur


class ConfirmationVerificationEmailSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=1024)
