from django.conf import settings
from django.db import models
class JournalAudit(models.Model):
    acteur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=100); cible=models.CharField(max_length=255); donnees=models.JSONField(default=dict); cree_le=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=("-cree_le",)
