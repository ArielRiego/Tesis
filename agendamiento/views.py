from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from cliente.models import Cliente
from servicios.models import Servicio
from usuarios.models import Usuario, TipoUsuario
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, connection
from .models import Cita, CitaServicio
from datetime import datetime, timedelta
import json
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_GET

@login_required
def menu_view(request):
    # Primero, vamos a verificar si esta vista se está llamando
    print("La vista menu_view se está ejecutando")
    clientes = Cliente.objects.all()
    context = {
        'clientes': clientes,
    }
    print(f"Número de clientes pasados al contexto: {len(clientes)}")  # Añade este print para debug
    return render(request, 'menu.html', context)

def obtener_clientes(request):
    clientes = Cliente.objects.all()
    data = [{'cedula': cliente.cedula, 'nombre': cliente.nombre, 'apellido': cliente.apellido} for cliente in clientes]
    return JsonResponse({'clientes': data})

def obtener_servicios(request):
    servicios = Servicio.objects.all()
    data = [{'id': servicio.idservicio, 'descripcion': servicio.descripcion, 'duracion': servicio.duracion, 'costo': servicio.costo} for servicio in servicios]
    return JsonResponse({'servicios': data})

def obtener_empleados(request):
    empleados = Usuario.objects.filter(usuario_administrador=False)
    data = [{'id': empleado.idusuario, 'nombre': empleado.nombre, 'apellido': empleado.apellido} for empleado in empleados]
    return JsonResponse({'empleados': data})

def obtener_id_servicio(request):
    nombre_servicio = request.GET.get('nombre')
    try:
        servicio = Servicio.objects.get(descripcion=nombre_servicio)
        return JsonResponse({'id': servicio.idservicio})
    except Servicio.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
from decimal import Decimal

def obtener_id_empleado(request):
    nombre_empleado = request.GET.get('nombre')
    nombre, apellido = nombre_empleado.split(' ', 1)
    try:
        empleado = TipoUsuario.objects.get(usuario__nombre=nombre, usuario__apellido=apellido)
        return JsonResponse({'id': empleado.idtipousuario})
    except TipoUsuario.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)

@require_POST
@csrf_exempt
def agregar_cita(request):
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            # Crear la cita principal
            cliente = Cliente.objects.get(cedula=data['idcliente'])
            fecha_hora_inicio = datetime.strptime(f"{data['fecha']} {data['hora_inicio']}", "%Y-%m-%d %H:%M")
            
            # Calcular la duración total y la hora de finalización
            duracion_total = sum(servicio['duracion'] for servicio in data['servicios'])
            fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion_total)
            
            cita = Cita.objects.create(
                idcliente=cliente,
                fecha=fecha_hora_inicio.date(),
                hora_inicio=fecha_hora_inicio.time(),
                hora_fin=fecha_hora_fin.time(),
                estado=data['estado'],
                tiempo_gracia=data['tiempo_gracia'],
                precio_total=Decimal(str(data['precio_total']))
            )
            
            # Crear los servicios asociados a la cita
            for servicio_data in data['servicios']:
                try:
                    servicio = Servicio.objects.get(idservicio=servicio_data['idservicio'])
                    tipo_usuario = TipoUsuario.objects.get(idtipousuario=servicio_data['idtipo_usuario'])
                    
                    # Usar SQL directo para insertar en cita_servicios
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO cita_servicios (idcita, idservicio, idtipo_usuario, duracion, costo)
                            VALUES (%s, %s, %s, %s, %s)
                        """, [
                            cita.idcita,  # Usamos idcita en lugar de id
                            servicio.idservicio,
                            tipo_usuario.idtipousuario,
                            servicio_data['duracion'],
                            Decimal(str(servicio_data['costo']))
                        ])
                except ObjectDoesNotExist as e:
                    # Si no se encuentra el servicio o el tipo de usuario, eliminamos la cita y lanzamos un error
                    cita.delete()
                    return JsonResponse({'success': False, 'error': f'Error: {str(e)}. Por favor, verifique los datos del servicio y del empleado.'})
        
        return JsonResponse({'success': True, 'message': 'Cita agendada con éxito'})
    
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'error': f'Error en el formato JSON: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@require_GET
def obtener_citas(request):
    citas = Cita.objects.all()
    eventos = []
    for cita in citas:
        eventos.append({
            'id': cita.idcita,
            'title': f'Cita para {cita.idcliente.nombre} {cita.idcliente.apellido}',
            'start': f'{cita.fecha}T{cita.hora_inicio}',
            'end': f'{cita.fecha}T{cita.hora_fin}',
            'allDay': False,
            'extendedProps': {
                'estado': cita.estado,
                'cliente': f'{cita.idcliente.nombre} {cita.idcliente.apellido}',
                'precio_total': str(cita.precio_total)
            }
        })
    return JsonResponse(eventos, safe=False)
    