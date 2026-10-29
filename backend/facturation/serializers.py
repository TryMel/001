from rest_framework import serializers
from .models import Abonnement, Facture
class AbonnementSerializer(serializers.ModelSerializer):
    class Meta: model=Abonnement; fields="__all__"; read_only_fields=("utilisateur",)
class FactureSerializer(serializers.ModelSerializer):
    class Meta: model=Facture; fields="__all__"; read_only_fields=("utilisateur","reference","statut")
