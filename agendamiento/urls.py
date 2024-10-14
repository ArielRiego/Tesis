from django.urls import path, include
from . import views

urlpatterns = [
    path('menu/', views.menu_view, name='menu'),
    path('obtener-clientes/', views.obtener_clientes, name='obtener_clientes'),
    path('obtener-servicios/', views.obtener_servicios, name='obtener_servicios'),
    path('obtener-empleados/', views.obtener_empleados, name='obtener_empleados'),
    path('agregar-cita/', views.agregar_cita, name='agregar_cita'),
    path('obtener-id-servicio/', views.obtener_id_servicio, name='obtener_id_servicio'),
    path('obtener-id-empleado/', views.obtener_id_empleado, name='obtener_id_empleado'),
    path('obtener-citas/', views.obtener_citas, name='obtener_citas'),
   # path('obtener-citas/', views.obtener_citas, name='obtener_citas'),
]
