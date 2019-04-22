from django.urls import path
from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.http import AsgiHandler
from yahtzeehints.views.games import Wait

urlpatterns = [
    path("games/wait/", Wait),
    url("^", AsgiHandler),
]

application = ProtocolTypeRouter({
    "http": URLRouter(urlpatterns),
})
