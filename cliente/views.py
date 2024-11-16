from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.contrib import messages
from .models import Cliente
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from agendamiento.models import Cita, CitaServicio
from django.http import JsonResponse
from usuarios.models import Usuario
import logging
from django.db import connection

logger = logging.getLogger(__name__)

def obtener_servicios_cita(request, id_cita):
    try:
        cita = get_object_or_404(Cita, idcita=id_cita)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.descripcion, cs.duracion, cs.costo
                FROM cita_servicios cs
                JOIN servicios s ON cs.idservicio = s.idservicio
                WHERE cs.idcita = %s
            """, [id_cita])
            servicios = cursor.fetchall()
        
        servicios_data = [{
            'descripcion': servicio[0],
            'duracion': servicio[1],
            'costo': float(servicio[2])
        } for servicio in servicios]
        
        return JsonResponse({
            'success': True,
            'servicios': servicios_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
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


def historial_cliente(request, cedula):
    cliente = get_object_or_404(Cliente, cedula=cedula)
    query = request.GET.get('q', '')
    estado_filtrado = request.GET.get('estado', '')
    # Obtener y formatear fechas
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    # Convertir fechas si están en formato dd/mm/aaaa
    try:
        if fecha_desde:
            fecha_desde = datetime.strptime(fecha_desde, '%d/%m/%Y').strftime('%Y-%m-%d')
        if fecha_hasta:
            fecha_hasta = datetime.strptime(fecha_hasta, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        # Si hay error en el formato, ignorar las fechas
        fecha_desde = ''
        fecha_hasta = ''
    empleado_filtrado = request.GET.get('empleado', '')

    with connection.cursor() as cursor:
        sql = """
        SELECT c.idcita, c.fecha, c.hora_inicio, c.estado, c.precio_total,
               u.nombre AS nombre_empleado, u.apellido AS apellido_empleado,
               array_agg(s.descripcion) as servicios
        FROM citas c
        LEFT JOIN usuario u ON c.idusuario = u.idusuario
        LEFT JOIN cita_servicios cs ON c.idcita = cs.idcita
        LEFT JOIN servicios s ON cs.idservicio = s.idservicio
        WHERE c.idcliente = %s
        """
        params = [cedula]

        if query:
            sql += " AND (LOWER(s.descripcion) LIKE LOWER(%s) OR LOWER(u.nombre) LIKE LOWER(%s) OR LOWER(u.apellido) LIKE LOWER(%s))"
            params.extend(['%' + query + '%'] * 3)

        if estado_filtrado:
            sql += " AND LOWER(c.estado) = LOWER(%s)"
            params.append(estado_filtrado)

        if fecha_desde:
            sql += " AND DATE(c.fecha) >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            sql += " AND DATE(c.fecha) <= %s"
            params.append(fecha_hasta)

        if empleado_filtrado:
            sql += " AND u.idusuario = %s"
            params.append(empleado_filtrado)

        sql += " GROUP BY c.idcita, c.fecha, c.hora_inicio, c.estado, c.precio_total, u.nombre, u.apellido ORDER BY c.fecha DESC, c.hora_inicio DESC"

        cursor.execute(sql, params)
        citas = cursor.fetchall()

    citas_formateadas = []
    for cita in citas:
        citas_formateadas.append({
            'idcita': cita[0],
            'fecha': cita[1],
            'hora_inicio': cita[2],
            'estado': cita[3],
            'precio_total': cita[4],
            'empleado': f"{cita[5]} {cita[6]}".strip() if cita[5] or cita[6] else "No especificado",
            'servicios': ', '.join(filter(None, cita[7])) if cita[7] else "Sin servicios"
        })

    empleados = Usuario.objects.all()  # Asumiendo que tienes un modelo Usuario

    context = {
        'cliente': cliente,
        'citas': citas_formateadas,
        'query': query,
        'estado_filtrado': estado_filtrado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'empleado_filtrado': empleado_filtrado,
        'empleados': empleados,
    }
    return render(request, 'menu_historial_cliente.html', context)

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