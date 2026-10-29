from rest_framework import serializers

from collaborations.models import Collaboration

from .models import Evaluation, Signalement, Verification


class EvaluationSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(
        source="auteur.get_full_name",
        read_only=True,
    )

    class Meta:
        model = Evaluation
        fields = (
            "id",
            "evalue",
            "auteur",
            "auteur_nom",
            "collaboration",
            "note",
            "commentaire",
            "statut",
            "cree_le",
        )
        read_only_fields = (
            "id",
            "auteur",
            "auteur_nom",
            "statut",
            "cree_le",
        )

    def validate_note(self, valeur):
        if not 1 <= valeur <= 5:
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
        return valeur

    def validate(self, donnees):
        if "statut" in self.initial_data:
            raise serializers.ValidationError(
                {"statut": "Le statut de l’avis est déterminé par le serveur."}
            )
        collaboration = donnees.get(
            "collaboration",
            getattr(self.instance, "collaboration", None),
        )
        utilisateur = self.context["request"].user
        evalue = donnees.get("evalue", getattr(self.instance, "evalue", None))
        if collaboration is None or collaboration.statut != Collaboration.Statut.TERMINEE:
            raise serializers.ValidationError(
                "Une collaboration terminée est requise pour publier un avis."
            )
        if utilisateur.pk not in (collaboration.client_id, collaboration.prestataire_id):
            raise serializers.ValidationError(
                "Seul un participant à la collaboration peut évaluer."
            )
        autre_partie_id = (
            collaboration.prestataire_id
            if utilisateur.pk == collaboration.client_id
            else collaboration.client_id
        )
        if evalue is None or evalue.pk != autre_partie_id:
            raise serializers.ValidationError(
                "L’avis doit porter sur l’autre participant à la collaboration."
            )
        if collaboration.evaluations.filter(
            auteur=utilisateur,
            evalue=evalue,
        ).exists():
            raise serializers.ValidationError(
                "Vous avez déjà évalué cette collaboration."
            )
        return donnees

    def create(self, donnees):
        return Evaluation.objects.create(
            auteur=self.context["request"].user,
            statut=Evaluation.Statut.PUBLIEE,
            **donnees,
        )


class EvaluationPubliqueSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(
        source="auteur.get_full_name",
        read_only=True,
    )

    class Meta:
        model = Evaluation
        fields = ("id", "auteur_nom", "note", "commentaire", "cree_le")


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = (
            "id",
            "utilisateur",
            "type",
            "statut",
            "reference_document",
            "commentaire",
            "cree_le",
        )
        read_only_fields = (
            "id",
            "utilisateur",
            "statut",
            "commentaire",
            "cree_le",
        )

    def validate(self, donnees):
        champs_proteges = {"statut", "commentaire"}.intersection(self.initial_data)
        if champs_proteges:
            raise serializers.ValidationError(
                {champ: "Ce champ est réservé à l’équipe de vérification." for champ in champs_proteges}
            )
        return donnees

    def create(self, donnees):
        return Verification.objects.create(
            utilisateur=self.context["request"].user,
            **donnees,
        )


class SignalementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signalement
        fields = (
            "id",
            "cible",
            "evaluation",
            "motif",
            "description",
            "statut",
            "cree_le",
        )
        read_only_fields = ("id", "statut", "cree_le")

    def validate(self, donnees):
        if "statut" in self.initial_data:
            raise serializers.ValidationError(
                {"statut": "Le statut du signalement est déterminé par la modération."}
            )
        cible = donnees.get("cible")
        evaluation = donnees.get("evaluation")
        if (cible is None) == (evaluation is None):
            raise serializers.ValidationError(
                "Choisissez exactement un compte ou un avis à signaler."
            )
        if evaluation and evaluation.auteur_id == self.context["request"].user.pk:
            raise serializers.ValidationError("Vous ne pouvez pas signaler votre propre avis.")
        return donnees

    def create(self, donnees):
        return Signalement.objects.create(
            auteur=self.context["request"].user,
            **donnees,
        )
