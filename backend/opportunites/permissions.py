from organisations.models import AppartenanceOrganisation


ROLES_RECRUTEMENT_ORGANISATION = (
    AppartenanceOrganisation.Role.PROPRIETAIRE,
    AppartenanceOrganisation.Role.RECRUTEUR,
)


def peut_gerer_organisation_recrutement(organisation, utilisateur):
    return AppartenanceOrganisation.objects.filter(
        organisation=organisation,
        utilisateur=utilisateur,
        role__in=ROLES_RECRUTEMENT_ORGANISATION,
    ).exists()


def peut_gerer_opportunite(opportunite, utilisateur):
    if opportunite.organisation_id is not None:
        return peut_gerer_organisation_recrutement(
            opportunite.organisation,
            utilisateur,
        )
    if opportunite.createur_id == utilisateur.pk:
        return True
    return False
