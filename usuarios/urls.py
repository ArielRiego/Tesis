"""
URL configuration for Peluqueria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# C:\Users\AGRA\Desktop\Tesis\usuarios\urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('menu/', views.menu_view, name='menu'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('empleados/', views.listar_empleados, name='listar_empleados'),
    path('empleados/agregar/', views.agregar_empleado, name='agregar_empleado'),
    path('empleados/editar/<int:idusuario>/', views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:idusuario>/', views.eliminar_empleado, name='eliminar_empleado'),
    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),
    path('empleado/<int:idusuario>/horario/', views.listar_horario_empleado, name='listar_horario_empleado'),
    path('guardar-horarios/', views.guardar_horarios, name='guardar_horarios'),
    path('api/tipos-permiso/', views.api_tipos_permiso, name='api_tipos_permiso'),
    path('guardar-permiso/', views.guardar_permiso, name='guardar_permiso'),

]
