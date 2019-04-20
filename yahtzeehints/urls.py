from django.urls import path
from yahtzeehints import views

urlpatterns = [
    path('', views.Main.as_view()),
]
