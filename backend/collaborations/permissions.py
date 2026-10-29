from organisations.models import AppartenanceOrganisation
from comptes.roles import utilisateur_a_role


def peut_gerer_demande(demande, utilisateur):
    if demande.client_id == utilisateur.pk:
        return True
    if demande.organisation_id is None:
        return False
    return AppartenanceOrganisation.objects.filter(
        organisation_id=demande.organisation_id,
        utilisateur=utilisateur,
        role__in=(
            AppartenanceOrganisation.Role.PROPRIETAIRE,
            AppartenanceOrganisation.Role.GESTIONNAIRE,
        ),
    ).exists()


def peut_proposer(utilisateur):
    if not utilisateur.is_active or not utilisateur_a_role(
        utilisateur, "professionnel"
    ):
        return False
    return hasattr(utilisateur, "profil")


def peut_gerer_collaboration(collaboration, utilisateur):
    if (
        collaboration.client_id == utilisateur.pk
        or collaboration.prestataire_id == utilisateur.pk
    ):
        return True
    return (
        collaboration.demande.organisation_id is not None
        and AppartenanceOrganisation.objects.filter(
            organisation_id=collaboration.demande.organisation_id,
            utilisateur=utilisateur,
            role__in=(
                AppartenanceOrganisation.Role.PROPRIETAIRE,
                AppartenanceOrganisation.Role.GESTIONNAIRE,
            ),
        ).exists()
    )


def represente_client_collaboration(collaboration, utilisateur):
    if collaboration.client_id == utilisateur.pk:
        return True
    return (
        collaboration.demande.organisation_id is not None
        and AppartenanceOrganisation.objects.filter(
            organisation_id=collaboration.demande.organisation_id,
            utilisateur=utilisateur,
            role__in=(
                AppartenanceOrganisation.Role.PROPRIETAIRE,
                AppartenanceOrganisation.Role.GESTIONNAIRE,
            ),
        ).exists()
    )
