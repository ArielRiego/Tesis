from django.urls import path
from . import views

urlpatterns = [
    path('servicio/', views.agregar_servicio, name='agregar_servicio'),
    path('servicios/', views.listar_servicios, name='listar_servicios'),
    path('servicios/editar/<int:idservicio>/', views.editar_servicio, name='editar_servicio'),
    path('servicios/eliminar/<int:idservicio>/', views.eliminar_servicio, name='eliminar_servicio'),
    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),
]

