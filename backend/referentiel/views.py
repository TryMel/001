from django.db.models import Q
from rest_framework import serializers, viewsets
from .models import Competence, Metier
from .serializers import CompetenceSerializer, MetierSerializer

class MetierVueSet(viewsets.ReadOnlyModelViewSet):
    queryset = Metier.objects.select_related("parent").all()
    serializer_class = MetierSerializer
    search_fields = ("nom", "code")

class CompetenceVueSet(viewsets.ReadOnlyModelViewSet):
    queryset = Competence.objects.prefetch_related("metiers").all()
    serializer_class = CompetenceSerializer
    search_fields = ("nom",)
    ordering_fields = ("nom",)
    ordering = ("nom",)

    def get_queryset(self):
        queryset = super().get_queryset()
        metier = self.request.query_params.get("metier")
        if metier:
            try:
                metier_id = int(metier)
            except ValueError as erreur:
                raise serializers.ValidationError(
                    {"metier": "Indiquez un identifiant de métier valide."}
                ) from erreur
            queryset = queryset.filter(
                Q(metiers__pk=metier_id) | Q(metiers__isnull=True)
            ).distinct()
        return queryset
