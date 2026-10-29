from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from analytique.models import EvenementInteraction


class Command(BaseCommand):
    help = "Supprime les clics analytiques plus anciens que la durée de conservation configurée."

    def handle(self, *args, **options):
        seuil = timezone.now() - timedelta(
            days=settings.ANALYTICS_RETENTION_DAYS
        )
        supprimes, _ = EvenementInteraction.objects.filter(cree_le__lt=seuil).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"{supprimes} événement(s) supprimé(s) avant "
                f"{timezone.localtime(seuil):%Y-%m-%d %H:%M}."
            )
        )
