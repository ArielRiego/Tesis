from django.urls import path
from . import views

urlpatterns = [
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/eliminar/<int:cedula>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/editar/<int:cedula>/', views.editar_cliente, name='editar_cliente'),
    path('cliente/', views.agregar_cliente, name='agregar_cliente'),
    path('clientes/historial/<int:cedula>/', views.historial_cliente, name='historial_cliente'),
    path('obtener-servicios-cita/<int:id_cita>/', views.obtener_servicios_cita, name='obtener_servicios_cita'),
]

