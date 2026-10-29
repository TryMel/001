from django.db import IntegrityError
from django.db.models import Q
from rest_framework import serializers, viewsets

from .models import (
    EntrepriseReference,
    EtablissementReference,
    Marche,
    ProgrammeFormationReference,
    RegleMetierLocale,
    Ville,
)
from .serializers import (
    EntrepriseReferenceSerializer,
    EtablissementReferenceSerializer,
    MarcheSerializer,
    ProgrammeFormationReferenceSerializer,
    RegleMetierLocaleSerializer,
    VilleSerializer,
)


class MarcheVueSet(viewsets.ReadOnlyModelViewSet):
    queryset = Marche.objects.filter(est_actif=True)
    serializer_class = MarcheSerializer


class RegleMetierLocaleVueSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegleMetierLocale.objects.filter(active=True)
    serializer_class = RegleMetierLocaleSerializer


class ReferenceLocaliseeVueSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset().filter(marche__est_actif=True)
        pays = self.request.query_params.get("pays")
        if pays:
            queryset = queryset.filter(marche__code_pays=pays.upper())
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save(cree_par=self.request.user)
        except IntegrityError as erreur:
            raise serializers.ValidationError(
                {"detail": "Cette valeur existe déjà pour ce pays."}
            ) from erreur


class VilleVueSet(ReferenceLocaliseeVueSet):
    queryset = Ville.objects.select_related("marche").all()
    serializer_class = VilleSerializer
    search_fields = ("nom",)
    ordering_fields = ("nom",)
    ordering = ("nom",)


class EntrepriseReferenceVueSet(ReferenceLocaliseeVueSet):
    queryset = EntrepriseReference.objects.select_related("marche").all()
    serializer_class = EntrepriseReferenceSerializer
    search_fields = ("nom",)
    ordering_fields = ("nom",)
    ordering = ("nom",)


class EtablissementReferenceVueSet(ReferenceLocaliseeVueSet):
    queryset = EtablissementReference.objects.select_related("marche").all()
    serializer_class = EtablissementReferenceSerializer
    search_fields = ("nom",)
    ordering_fields = ("nom", "type")
    ordering = ("nom",)


class ProgrammeFormationReferenceVueSet(ReferenceLocaliseeVueSet):
    queryset = ProgrammeFormationReference.objects.select_related(
        "marche",
        "etablissement",
    ).prefetch_related("metiers")
    serializer_class = ProgrammeFormationReferenceSerializer
    search_fields = ("intitule", "etablissement__nom", "metiers__nom")
    ordering_fields = ("intitule", "niveau")
    ordering = ("intitule",)

    def get_queryset(self):
        queryset = super().get_queryset()
        etablissement = self.request.query_params.get("etablissement")
        metier = self.request.query_params.get("metier")
        if etablissement:
            try:
                etablissement_id = int(etablissement)
            except ValueError as erreur:
                raise serializers.ValidationError(
                    {"etablissement": "Indiquez un identifiant valide."}
                ) from erreur
            queryset = queryset.filter(etablissement_id=etablissement_id)
        if metier:
            try:
                metier_id = int(metier)
            except ValueError as erreur:
                raise serializers.ValidationError(
                    {"metier": "Indiquez un identifiant valide."}
                ) from erreur
            queryset = queryset.filter(
                Q(metiers__pk=metier_id) | Q(metiers__isnull=True)
            ).distinct()
        return queryset
