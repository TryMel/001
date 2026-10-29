from rest_framework.routers import DefaultRouter
from .views import NotificationVueSet
routeur=DefaultRouter(); routeur.register("",NotificationVueSet,basename="notification")
urlpatterns=routeur.urls
