from rest_framework.routers import DefaultRouter
from .views import AbonnementVueSet, FactureVueSet
routeur=DefaultRouter(); routeur.register("abonnements",AbonnementVueSet,basename="abonnement"); routeur.register("factures",FactureVueSet,basename="facture")
urlpatterns=routeur.urls
