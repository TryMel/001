from comptes.roles import ROLES_FONCTIONNELS


ROLES_AVEC_PROFIL_PROFESSIONNEL = frozenset(
    ("professionnel", "candidat", "etudiant")
)
assert ROLES_AVEC_PROFIL_PROFESSIONNEL.issubset(set(ROLES_FONCTIONNELS))


def utilisateur_peut_gerer_profil(utilisateur):
    return any(
        role in ROLES_AVEC_PROFIL_PROFESSIONNEL
        for role in utilisateur.roles_professionnels
    )
