from django.urls import path
from yahtzeehints import views
from django.views import static
from django.conf import settings

urlpatterns = [
    path('', views.Index.as_view()),
    path('hint/', views.Hint.as_view()),
    path('bundle.min.js', static.serve, dict(path='bundle.min.js', document_root=settings.STATIC_ROOT)),
]
