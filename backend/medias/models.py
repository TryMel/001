from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ImageContenu(models.Model):
    type_contenu = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    contenu_id = models.PositiveBigIntegerField()
    contenu = GenericForeignKey("type_contenu", "contenu_id")
    fichier = models.ImageField(upload_to="contenus/")
    position = models.PositiveSmallIntegerField()
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("type_contenu", "contenu_id", "position"),
                name="image_contenu_position_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(position__lt=5),
                name="image_contenu_position_max_4",
            ),
        ]
