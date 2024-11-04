from django.urls import path
from . import views



urlpatterns = [
    path('', views.menu_pago, name='menu_pago'),
    path('citas-pendientes/', views.citas_pendientes, name='citas_pendientes'),
    path('obtener-datos-cita/<int:id_cita>/', views.obtener_datos_cita, name='obtener_datos_cita'),
    path('procesar/', views.procesar_pago, name='procesar_pago'),
    path('detalle/<int:idpago>/', views.detalle_pago, name='detalle_pago'),
    path('editar/<int:idpago>/', views.editar_pago, name='editar_pago'),
    path('eliminar/<int:idpago>/', views.eliminar_pago, name='eliminar_pago'),
    path('lista/', views.lista_pagos, name='lista_pagos'),
    path('obtener-datos-pago/<int:idpago>/', views.obtener_datos_pago, name='obtener_datos_pago'),
    path('pagos/procesar/', views.procesar_pago, name='procesar_pago'),
]