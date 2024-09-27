from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Servicio  # Importar el modelo Servicio
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q



@login_required
def agregar_servicio(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        duracion = request.POST.get('duracion')
        costo = request.POST.get('costo')

        # Crear y guardar el servicio en la base de datos
        servicio = Servicio(descripcion=descripcion, duracion=duracion, costo=costo)
        servicio.save()

        messages.success(request, 'Servicio agregado exitosamente')
        return redirect('/servicios/')  # Redirige a la misma página o a donde prefieras

    return render(request, 'menu_agregar_servicio.html')


@login_required
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
    return render(request, 'menu_servicios.html', {'servicios': servicios, 'query': query})

@login_required
def editar_servicio(request, idservicio):
    servicio = get_object_or_404(Servicio, idservicio=idservicio)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        duracion = request.POST.get('duracion')
        costo = request.POST.get('costo')

        # Actualizar los campos del servicio
        servicio.descripcion = descripcion
        servicio.duracion = duracion
        servicio.costo = costo
        servicio.save()

        messages.success(request, 'Servicio actualizado exitosamente')
        return redirect('/servicios/')  # Redirige a la lista de servicios

    return render(request, 'menu_editar_servicios.html', {'servicio': servicio})

@login_required
def eliminar_servicio(request, idservicio):
    servicio = get_object_or_404(Servicio, idservicio=idservicio)
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'Servicio eliminado exitosamente')
        return redirect('/servicios/')  # Redirige a la lista de servicios
    return render(request, 'menu_eliminar_servicios.html', {'servicio': servicio})
