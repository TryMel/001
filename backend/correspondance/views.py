from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RechercheProfilsQuerySerializer, ResultatRechercheProfilsSerializer
from .services import classer_profils


class RechercheProfilsVue(APIView):
    @extend_schema(
        tags=["Correspondance"],
        parameters=[
            OpenApiParameter("competence", int, OpenApiParameter.QUERY, many=True),
            OpenApiParameter("ville", str, OpenApiParameter.QUERY),
            OpenApiParameter("disponible", bool, OpenApiParameter.QUERY),
        ],
        responses=ResultatRechercheProfilsSerializer(many=True),
        description="Classe les profils rendus publics selon les compétences demandées, la ville et la disponibilité.",
    )
    def get(self, request):
        parametres = RechercheProfilsQuerySerializer(data=request.query_params)
        parametres.is_valid(raise_exception=True)
        donnees = parametres.validated_data
        resultats = classer_profils(
            donnees.get("competence", []),
            donnees.get("ville", ""),
            donnees.get("disponible"),
        )
        reponse = [
            {
                "profil": ligne["profil"],
                "score": ligne["score"],
                "explication": ligne["explication"],
            }
            for ligne in resultats
        ]
        return Response(ResultatRechercheProfilsSerializer(reponse, many=True).data)
