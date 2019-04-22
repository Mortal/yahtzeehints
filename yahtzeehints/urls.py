from django.urls import path
from yahtzeehints import views

urlpatterns = [
    path('hint/', views.Hint.as_view()),
]
