from django.conf import settings
from django.db import models
class Notification(models.Model):
    utilisateur=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="notifications")
    titre=models.CharField(max_length=180); message=models.TextField(); lien=models.CharField(max_length=255,blank=True); lue_le=models.DateTimeField(null=True,blank=True); cree_le=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=("-cree_le",)
