from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Notification
from .serializers import NotificationSerializer
class NotificationVueSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=NotificationSerializer
    def get_queryset(self): return Notification.objects.filter(utilisateur=self.request.user)
    @action(detail=True,methods=["post"])
    def lire(self,request,pk=None):
        notification=self.get_object(); notification.lue_le=timezone.now(); notification.save(update_fields=["lue_le"]); return Response(NotificationSerializer(notification).data)
