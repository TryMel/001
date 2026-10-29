from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from configuration.medias import compresser_image

from .models import ImageContenu


class ImagesUrlMixin(serializers.ModelSerializer):
    def get_images_url(self, contenu):
        request = self.context.get("request")
        urls = []
        for image in contenu.images.all():
            url = image.fichier.url
            urls.append(request.build_absolute_uri(url) if request else url)
        return urls


class GalerieImagesMixin(ImagesUrlMixin):
    def validate_images(self, images):
        return [compresser_image(image) for image in images]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        contenu = super().create(validated_data)
        self._remplacer_images(contenu, images)
        return contenu

    def update(self, instance, validated_data):
        remplacer_images = "images" in validated_data
        images = validated_data.pop("images", [])
        contenu = super().update(instance, validated_data)
        if remplacer_images:
            self._remplacer_images(contenu, images)
        return contenu

    @staticmethod
    def _remplacer_images(contenu, images):
        contenu.images.all().delete()
        type_contenu = ContentType.objects.get_for_model(contenu)
        ImageContenu.objects.bulk_create(
            [
                ImageContenu(
                    type_contenu=type_contenu,
                    contenu_id=contenu.pk,
                    fichier=image,
                    position=position,
                )
                for position, image in enumerate(images)
            ]
        )
