from rest_framework import viewsets
from .models import Ressource
from .serializers import RessourceSerializer
class RessourceVueSet(viewsets.ModelViewSet):
    serializer_class=RessourceSerializer; search_fields=("titre","contenu","metier__nom")
    def get_queryset(self): return Ressource.objects.filter(publiee=True) | Ressource.objects.filter(auteur=self.request.user)
