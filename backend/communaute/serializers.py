from rest_framework import serializers
from .models import Ressource
class RessourceSerializer(serializers.ModelSerializer):
    class Meta: model=Ressource; fields="__all__"; read_only_fields=("auteur","publiee")
    def create(self,donnees): return Ressource.objects.create(auteur=self.context["request"].user,**donnees)
