from rest_framework import viewsets
from .models import Abonnement, Facture
from .serializers import AbonnementSerializer, FactureSerializer
class AbonnementVueSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=AbonnementSerializer
    def get_queryset(self): return Abonnement.objects.filter(utilisateur=self.request.user)
class FactureVueSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=FactureSerializer
    def get_queryset(self): return Facture.objects.filter(utilisateur=self.request.user)
