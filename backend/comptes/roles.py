ROLES_AKASHA = (
    ("professionnel", "Professionnel"),
    ("client", "Client"),
    ("candidat", "Candidat"),
    ("recruteur", "Recruteur"),
    ("etudiant", "Étudiant"),
    ("organisation", "Organisation"),
    ("etablissement", "Établissement"),
)
ROLES_FONCTIONNELS = tuple(role for role, _ in ROLES_AKASHA)


def utilisateur_a_role(utilisateur, *roles):
    roles_attribues = set(getattr(utilisateur, "roles_professionnels", []) or [])
    return bool(roles_attribues.intersection(roles))
