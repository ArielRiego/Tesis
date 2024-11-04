from django.urls import path
from . import views

urlpatterns = [
    path('servicios-populares/', views.obtener_reporte_servicios_populares, name='servicios_populares'),
]

