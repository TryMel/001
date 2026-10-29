from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps
from rest_framework import serializers


TAILLE_MAXIMALE_IMAGE = 5 * 1024 * 1024
FORMATS_IMAGE_AUTORISES = {
    "JPEG": ("jpg", {}),
    "PNG": ("png", {"optimize": True}),
    "WEBP": ("webp", {"quality": 82, "method": 6}),
}
DIMENSIONS_MAXIMALES_IMAGE = (1600, 1600)


def compresser_image(image_televersee):
    if image_televersee is None:
        return None
    if image_televersee.size > TAILLE_MAXIMALE_IMAGE:
        raise serializers.ValidationError("L’image ne doit pas dépasser 5 Mo.")

    sortie = BytesIO()
    image_televersee.seek(0)
    with Image.open(image_televersee) as source:
        format_source = source.format
        if format_source not in FORMATS_IMAGE_AUTORISES:
            raise serializers.ValidationError(
                "Utilisez une image JPEG, PNG ou WebP."
            )

        image = ImageOps.exif_transpose(source)
        image.thumbnail(DIMENSIONS_MAXIMALES_IMAGE, Image.Resampling.LANCZOS)
        options = dict(FORMATS_IMAGE_AUTORISES[format_source][1])
        if format_source == "JPEG":
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            options.update(quality=82, optimize=True, progressive=True)

        image.save(sortie, format=format_source, **options)
    extension = FORMATS_IMAGE_AUTORISES[format_source][0]
    return ContentFile(sortie.getvalue(), name=f"{uuid4().hex}.{extension}")


def supprimer_ancienne_image(instance, nom_champ, ancien_nom):
    image_actuelle = getattr(instance, nom_champ)
    if ancien_nom and (not image_actuelle or image_actuelle.name != ancien_nom):
        instance._meta.get_field(nom_champ).storage.delete(ancien_nom)
