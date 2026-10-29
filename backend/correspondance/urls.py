from django.urls import path
from .views import RechercheProfilsVue
urlpatterns=[path("profils/",RechercheProfilsVue.as_view())]
