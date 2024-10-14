from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q
from .models import Servicio, ServicioTipoUsuario
from usuarios.models import TipoUsuario  # Asegúrate de que esta ruta de importación sea correcta

def es_superusuario(user):
    return user.is_authenticated and user.usuario_administrador

def superuser_required(view_func):
    decorated_view_func = user_passes_test(es_superusuario, login_url='acceso_denegado')(view_func)
    return login_required(decorated_view_func)

@login_required
@superuser_required
def agregar_servicio(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        duracion = request.POST.get('duracion')
        costo = request.POST.get('costo')
        tipos_usuario = request.POST.getlist('tipos_usuario')

        servicio = Servicio(descripcion=descripcion, duracion=duracion, costo=costo)
        servicio.save()

        for tipo_id in tipos_usuario:
            tipo = TipoUsuario.objects.get(idtipousuario=tipo_id)
            ServicioTipoUsuario.objects.create(servicio=servicio, tipo_usuario=tipo)

        messages.success(request, 'Servicio agregado exitosamente')
        return redirect('listar_servicios')

    tipos_usuario = TipoUsuario.objects.all()
    return render(request, 'menu_agregar_servicio.html', {'tipos_usuario': tipos_usuario})

@login_required
def listar_servicios(request):
    query = request.GET.get('q', '')
    if query:
        servicios = Servicio.objects.filter(
            Q(descripcion__icontains=query) |
            Q(duracion__icontains=query) |
            Q(costo__icontains=query)
        )
    else:
        servicios = Servicio.objects.all()
    
    puede_editar = es_superusuario(request.user)
    
    servicios_con_tipos = []
    for servicio in servicios:
        tipos = ServicioTipoUsuario.objects.filter(servicio=servicio).values_list('tipo_usuario__descripcion', flat=True)
        servicios_con_tipos.append({
            'servicio': servicio,
            'tipos_usuario': list(tipos)
        })
    
    return render(request, 'menu_servicios.html', {
        'servicios': servicios_con_tipos, 
        'query': query,
        'puede_editar': puede_editar
    })

@login_required
@superuser_required
def editar_servicio(request, idservicio):
    servicio = get_object_or_404(Servicio, idservicio=idservicio)
    tipos_usuario_actuales = ServicioTipoUsuario.objects.filter(servicio=servicio).values_list('tipo_usuario__idtipousuario', flat=True)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        duracion = request.POST.get('duracion')
        costo = request.POST.get('costo')
        nuevos_tipos_usuario = request.POST.getlist('tipos_usuario')

        servicio.descripcion = descripcion
        servicio.duracion = duracion
        servicio.costo = costo
        servicio.save()

        # Eliminar tipos de usuario que ya no están seleccionados
        ServicioTipoUsuario.objects.filter(servicio=servicio).exclude(tipo_usuario__idtipousuario__in=nuevos_tipos_usuario).delete()

        # Añadir nuevos tipos de usuario
        for tipo_id in nuevos_tipos_usuario:
            ServicioTipoUsuario.objects.get_or_create(
                servicio=servicio,
                tipo_usuario=TipoUsuario.objects.get(idtipousuario=tipo_id)
            )

        messages.success(request, 'Servicio actualizado exitosamente')
        return redirect('listar_servicios')

    todos_tipos_usuario = TipoUsuario.objects.all()
    return render(request, 'menu_editar_servicios.html', {
        'servicio': servicio,
        'tipos_usuario': todos_tipos_usuario,
        'tipos_usuario_actuales': tipos_usuario_actuales
    })

@login_required
@superuser_required
def eliminar_servicio(request, idservicio):
    servicio = get_object_or_404(Servicio, idservicio=idservicio)
    if request.method == 'POST':
        # La eliminación en cascada se encargará de eliminar las relaciones en ServicioTipoUsuario
        servicio.delete()
        messages.success(request, 'Servicio eliminado exitosamente')
        return redirect('listar_servicios')
    return render(request, 'menu_eliminar_servicios.html', {'servicio': servicio})

@login_required
def acceso_denegado(request):
    user = request.user
    context = {
        'user_name': user.username,
        'user_email': user.mail,
        'user_role': 'Administrador' if user.usuario_administrador else 'Usuario Regular'
    }
    return render(request, 'acceso_denegado.html', context)