from rest_framework.routers import DefaultRouter
from .views import CandidatureVueSet, OpportuniteVueSet
routeur = DefaultRouter(); routeur.register("candidatures", CandidatureVueSet, basename="candidature"); routeur.register("", OpportuniteVueSet)
urlpatterns = routeur.urls
