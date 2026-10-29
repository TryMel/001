import logging
import uuid

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("django.request")


def gestionnaire_exceptions(exception, contexte):
    reponse = exception_handler(exception, contexte)
    if reponse is None:
        requete = contexte.get("request")
        identifiant_requete = uuid.uuid4().hex
        logger.exception(
            "Unhandled API exception",
            extra={
                "status_code": 500,
                "request_id": identifiant_requete,
                "request_path": requete.path if requete else "",
            },
        )
        return Response(
            {
                "code": "erreur_interne",
                "detail": "Une erreur interne est survenue.",
                "request_id": identifiant_requete,
            },
            status=500,
        )
    detail = reponse.data.get("detail", "La requête est invalide.") if isinstance(reponse.data, dict) else "La requête est invalide."
    reponse.data = {"code": getattr(exception, "default_code", "erreur_requete"), "detail": detail, "erreurs": reponse.data}
    return reponse
