from profils.models import ProfilProfessionnel

def classer_profils(competence_ids, ville="", disponible=None):
    profils = (
        ProfilProfessionnel.objects.filter(visible_publiquement=True)
        .select_related("utilisateur", "metier")
        .prefetch_related("niveaucompetence_set__competence")
    )
    if ville: profils=profils.filter(ville__iexact=ville)
    if disponible is not None: profils=profils.filter(disponible=disponible)
    demandes=set(map(int,competence_ids))
    resultat=[]
    for profil in profils:
        possede={niveau.competence_id for niveau in profil.niveaucompetence_set.all()}
        commun=len(demandes & possede)
        couverture=round(100 * commun / len(demandes)) if demandes else 0
        points=commun * 10 + (2 if profil.disponible else 0) + (3 if profil.utilisateur.est_verifie else 0)
        resultat.append({"profil": profil, "score": points, "explication": {"competences_correspondantes": commun, "competences_demandees": len(demandes), "couverture_pourcent": couverture, "disponible": profil.disponible, "identite_verifiee": profil.utilisateur.est_verifie}})
    return sorted(
        resultat,
        key=lambda ligne: (-ligne["score"], ligne["profil"].id),
    )
