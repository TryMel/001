from rest_framework.routers import DefaultRouter
from .views import RessourceVueSet
routeur=DefaultRouter(); routeur.register("ressources",RessourceVueSet,basename="ressource")
urlpatterns=routeur.urls
