from django.urls import path

from .views import EnregistrerInteractionVue

urlpatterns = [
    path("evenements/", EnregistrerInteractionVue.as_view(), name="evenement-interaction"),
]
