from rest_framework.routers import DefaultRouter
from .views import CompetenceVueSet, MetierVueSet
routeur = DefaultRouter(); routeur.register("metiers", MetierVueSet); routeur.register("competences", CompetenceVueSet)
urlpatterns = routeur.urls
