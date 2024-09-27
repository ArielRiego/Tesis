from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cliente
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q

@require_http_methods(["GET", "POST"])
def agregar_cliente(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        email = request.POST.get('email')
        ruc = request.POST.get('ruc')

        # Validar campos únicos
        if Cliente.objects.filter(cedula=cedula).exists():
            messages.error(request, 'Ya existe un cliente con esta cédula.')
            return render(request, 'menu_agregar_cliente.html', {'form_data': request.POST})

        if Cliente.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe un cliente con este correo electrónico.')
            return render(request, 'menu_agregar_cliente.html', {'form_data': request.POST})

        if Cliente.objects.filter(ruc=ruc).exists():
            messages.error(request, 'Ya existe un cliente con este RUC.')
            return render(request, 'menu_agregar_cliente.html', {'form_data': request.POST})

        if not is_valid_email(email):
            messages.error(request, 'El formato del correo electrónico no es válido.')
            return render(request, 'menu_agregar_cliente.html', {'form_data': request.POST})

        try:
            cliente = Cliente(
                cedula=cedula,
                nombre=request.POST.get('nombre'),
                apellido=request.POST.get('apellido'),
                email=email,
                ruc=ruc,
                telefono=request.POST.get('telefono')
            )
            cliente.full_clean()  # Realiza todas las validaciones del modelo
            cliente.save()
            messages.success(request, 'Cliente agregado exitosamente')
            return redirect('listar_clientes')
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'menu_agregar_cliente.html', {'form_data': request.POST})

    return render(request, 'menu_agregar_cliente.html')

def listar_clientes(request):
    query = request.GET.get('q', '')
    if query:
        clientes = Cliente.objects.filter(
            Q(cedula__icontains=query) |
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(email__icontains=query) |
            Q(ruc__icontains=query) |
            Q(telefono__icontains=query)
        )
    else:
        clientes = Cliente.objects.all()
    return render(request, 'menu_cliente.html', {'clientes': clientes, 'query': query})

@require_http_methods(["GET", "POST"])
def editar_cliente(request, cedula):
    cliente = get_object_or_404(Cliente, cedula=cedula)
    if request.method == 'POST':
        email = request.POST.get('email')
        ruc = request.POST.get('ruc')

        # Validar campos únicos (excluyendo el cliente actual)
        if Cliente.objects.exclude(cedula=cedula).filter(email=email).exists():
            messages.error(request, 'Ya existe otro cliente con este correo electrónico.')
            return render(request, 'menu_editar_cliente.html', {'cliente': cliente, 'form_data': request.POST})

        if Cliente.objects.exclude(cedula=cedula).filter(ruc=ruc).exists():
            messages.error(request, 'Ya existe otro cliente con este RUC.')
            return render(request, 'menu_editar_cliente.html', {'cliente': cliente, 'form_data': request.POST})

        # Validar formato de email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'El formato del correo electrónico no es válido.')
            return render(request, 'menu_editar_cliente.html', {'cliente': cliente, 'form_data': request.POST})

        try:
            cliente.nombre = request.POST.get('nombre')
            cliente.apellido = request.POST.get('apellido')
            cliente.email = email
            cliente.ruc = ruc
            cliente.telefono = request.POST.get('telefono')
            cliente.full_clean()  # Realiza todas las validaciones del modelo
            cliente.save()
            messages.success(request, 'Cliente actualizado exitosamente')
            return redirect('listar_clientes')
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'menu_editar_cliente.html', {'cliente': cliente, 'form_data': request.POST})

    return render(request, 'menu_editar_cliente.html', {'cliente': cliente})

@require_http_methods(["GET", "POST"])
def eliminar_cliente(request, cedula):
    cliente = get_object_or_404(Cliente, cedula=cedula)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente')
        return redirect('listar_clientes')
    return render(request, 'menu_eliminar_cliente.html', {'cliente': cliente})

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False