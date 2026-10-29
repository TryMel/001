from django.conf import settings
from django.db import models
from referentiel.models import Metier
class Ressource(models.Model):
    auteur=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="ressources")
    titre=models.CharField(max_length=180); contenu=models.TextField(); metier=models.ForeignKey(Metier,null=True,blank=True,on_delete=models.SET_NULL); publiee=models.BooleanField(default=False); cree_le=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=("-cree_le",)
