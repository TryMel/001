from rest_framework.routers import DefaultRouter
from .views import ConversationVueSet, MessageVueSet
routeur = DefaultRouter(); routeur.register("conversations", ConversationVueSet, basename="conversation"); routeur.register("messages", MessageVueSet, basename="message")
urlpatterns = routeur.urls
