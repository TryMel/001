from rest_framework.routers import DefaultRouter
from .views import ExperienceVueSet, FormationVueSet, QualificationVueSet, RealisationVueSet
routeur=DefaultRouter(); routeur.register("formations",FormationVueSet); routeur.register("experiences",ExperienceVueSet); routeur.register("realisations",RealisationVueSet); routeur.register("qualifications",QualificationVueSet)
urlpatterns=routeur.urls
