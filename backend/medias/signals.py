from collaborations.models import DemandeService, OffreService
from django.db.models.signals import post_delete
from django.dispatch import receiver
from organisations.models import Organisation
from profils.models import ProfilProfessionnel

from .models import ImageContenu


@receiver(post_delete, sender=ImageContenu)
def supprimer_fichier_image_contenu(sender, instance, **kwargs):
    if instance.fichier:
        instance.fichier.delete(save=False)


def supprimer_photo_principale(sender, instance, **kwargs):
    photo = getattr(instance, "photo", None)
    if photo:
        photo.delete(save=False)


for modele in (
    DemandeService,
    OffreService,
    Organisation,
    ProfilProfessionnel,
):
    post_delete.connect(
        supprimer_photo_principale,
        sender=modele,
        dispatch_uid=f"medias.supprimer_photo_{modele._meta.label_lower}",
    )
