from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from cliente.models import Cliente
from servicios.models import Servicio
from usuarios.models import Usuario, TipoUsuario, UsuarioTipoUsuario, Ausencia, HorarioTrabajo
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction, connection
from .models import Cita, CitaServicio
from datetime import datetime, timedelta
import json
from datetime import datetime, date
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_GET
from .whatsapp_service import whatsapp_service
from django.db.models import F, Sum
import logging


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

@login_required
def servicios_inmediatos(request):

    return render(request, 'menu_servicios_inmediatos.html')

def obtener_clientes(request):
    clientes = Cliente.objects.all()
    data = [{'cedula': cliente.cedula, 'nombre': cliente.nombre, 'apellido': cliente.apellido} for cliente in clientes]
    return JsonResponse({'clientes': data})

def obtener_servicios(request):
    servicios = Servicio.objects.all()
    data = [{'id': servicio.idservicio, 'descripcion': servicio.descripcion, 'duracion': servicio.duracion, 'costo': servicio.costo} for servicio in servicios]
    return JsonResponse({'servicios': data})

logger = logging.getLogger(__name__)

def obtener_empleados(request):
    fecha = request.GET.get('fecha')
    hora = request.GET.get('hora')
    nombre_servicio = request.GET.get('id_servicio')
    
    logger.info(f"Parámetros recibidos: fecha={fecha}, hora={hora}, id_servicio={nombre_servicio}")

    if not all([fecha, hora, nombre_servicio]):
        logger.error("Faltan parámetros requeridos")
        return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)

    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        hora_obj = datetime.strptime(hora, '%H:%M').time()
        dia_semana = fecha_obj.isoweekday()
        logger.info(f"Fecha procesada: {fecha_obj}, Hora: {hora_obj}, Día de la semana: {dia_semana}")

        try:
            servicio = Servicio.objects.get(descripcion=nombre_servicio)
            id_servicio = servicio.idservicio
            logger.info(f"Servicio encontrado: {nombre_servicio}, ID: {id_servicio}")
        except Servicio.DoesNotExist:
            logger.error(f"Servicio no encontrado: {nombre_servicio}")
            return JsonResponse({'error': f'Servicio "{nombre_servicio}" no encontrado'}, status=404)

        with connection.cursor() as cursor:
            query = """
            SELECT DISTINCT u.idusuario, u.nombre, u.apellido
            FROM usuario u
            JOIN usuario_tipo_usuario utu ON u.idusuario = utu.idusuario
            JOIN tipo_usuario tu ON utu.idtipousuario = tu.idtipousuario
            JOIN horario_trabajo ht ON u.idusuario = ht.idusuario
            JOIN servicio_tipo_usuario stu ON tu.idtipousuario = stu.idtipousuario
            LEFT JOIN ausencias a ON u.idusuario = a.idusuario
            WHERE u.usuario_administrador = FALSE
            AND ht.dia_semana = %s
            AND ht.hora_inicio <= %s
            AND ht.hora_fin >= %s
            AND stu.idservicio = %s
            AND (a.id IS NULL OR 
                 a.fecha_inicio > %s OR 
                 a.fecha_fin < %s OR 
                 a.aprobado = FALSE)
            """
            params = [dia_semana, hora_obj, hora_obj, id_servicio, 
                      datetime.combine(fecha_obj, hora_obj), 
                      datetime.combine(fecha_obj, hora_obj)]
            
            logger.info(f"Ejecutando query: {query}")
            logger.info(f"Parámetros de la query: {params}")
            
            cursor.execute(query, params)
            empleados_disponibles = cursor.fetchall()

        logger.info(f"Empleados disponibles encontrados: {len(empleados_disponibles)}")
        for emp in empleados_disponibles:
            logger.info(f"Empleado: ID={emp[0]}, Nombre={emp[1]}, Apellido={emp[2]}")
        
        data = [{'id': emp[0], 'nombre': emp[1], 'apellido': emp[2]} for emp in empleados_disponibles]
        return JsonResponse({'empleados': data})

    except ValueError as e:
        logger.error(f"Error en el formato de los datos: {str(e)}")
        return JsonResponse({'error': f'Error en el formato de los datos: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Error interno del servidor: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno del servidor: {str(e)}'}, status=500)

#logica para empleaos y horario

#fin logica


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


logger = logging.getLogger(__name__)

@login_required 
@require_POST
@csrf_exempt
def agregar_servicio_inmediato(request):
    try:
        data = json.loads(request.body)
        logger.info(f"Datos recibidos: {data}")
        
        with transaction.atomic():
            # Crear la cita principal para el servicio inmediato
            cliente = Cliente.objects.get(cedula=data['idcliente'])
            fecha_hora_actual = datetime.now()
            
            # Calcular la duración total y la hora de finalización
            duracion_total = sum(servicio['duracion'] for servicio in data['servicios'])
            fecha_hora_fin = fecha_hora_actual + timedelta(minutes=duracion_total)
            
            cita = Cita.objects.create(
                idcliente=cliente,
                fecha=fecha_hora_actual.date(),
                hora_inicio=fecha_hora_actual.time(),
                hora_fin=fecha_hora_fin.time(),
                estado='En progreso',
                tiempo_gracia=0,
                precio_total=Decimal(sum(Decimal(str(servicio['costo'])) for servicio in data['servicios'])),
                es_agendada=False,
                idusuario=request.user,
            )
            
            # Crear los servicios asociados a la cita
            servicios_nombres = []
            for servicio_data in data['servicios']:
                try:
                    servicio = Servicio.objects.get(idservicio=servicio_data['idservicio'])
                    usuario = Usuario.objects.get(idusuario=servicio_data['idtipo_usuario'])
                    
                    # Obtener el TipoUsuario del usuario
                    usuario_tipo_usuario = UsuarioTipoUsuario.objects.filter(usuario=usuario).first()
                    if not usuario_tipo_usuario:
                        raise ObjectDoesNotExist(f"El usuario {usuario.idusuario} no tiene un tipo asignado")
                    
                    tipo_usuario = usuario_tipo_usuario.tipo_usuario
                    
                    # Verificar si el tipo de usuario puede realizar este servicio
                    tipos_usuario_autorizados = servicio.tipos_usuario.all()
                    if not tipos_usuario_autorizados.filter(idtipousuario=tipo_usuario.idtipousuario).exists():
                        tipos_autorizados = ", ".join([str(t.idtipousuario) for t in tipos_usuario_autorizados])
                        raise ObjectDoesNotExist(f"El tipo de usuario {tipo_usuario.idtipousuario} no está autorizado para el servicio {servicio.idservicio}. Tipos autorizados: {tipos_autorizados}")
                    
                    # Usar SQL directo para insertar en cita_servicios
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO cita_servicios (idcita, idservicio, idtipo_usuario, duracion, costo)
                            VALUES (%s, %s, %s, %s, %s)
                        """, [
                            cita.idcita,
                            servicio.idservicio,
                            tipo_usuario.idtipousuario,
                            servicio_data['duracion'],
                            Decimal(str(servicio_data['costo']))
                        ])
                    servicios_nombres.append(servicio.descripcion)
                except ObjectDoesNotExist as e:
                    # Si no se encuentra el servicio o el tipo de usuario, eliminamos la cita y lanzamos un error
                    cita.delete()
                    error_message = f'Error: {str(e)}. Por favor, verifique los datos del servicio y del empleado.'
                    logger.error(f"ObjectDoesNotExist error: {error_message}")
                    return JsonResponse({'success': False, 'error': error_message})
        
        mensaje = f"Servicio inmediato registrado para {cliente.nombre}. "
        mensaje += f"Servicios: {', '.join(servicios_nombres)}. "
        mensaje += f"Duración total: {duracion_total} minutos. Precio total: ${cita.precio_total}."
        logger.info(mensaje)
        
        return JsonResponse({'success': True, 'message': 'Servicio inmediato registrado con éxito'})
    
    except json.JSONDecodeError as e:
        logger.error(f"Error en el formato JSON: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error en el formato JSON: {str(e)}'})
    except Exception as e:
        error_message = f'Error inesperado: {str(e)}'
        logger.error(f"Unexpected error: {error_message}")
        return JsonResponse({'success': False, 'error': error_message})
    
@login_required  
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
                precio_total=Decimal(str(data['precio_total'])),
                es_agendada=True,
                idusuario=request.user,
            )
            
            # Crear los servicios asociados a la cita
            servicios_nombres = []
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
                            cita.idcita,
                            servicio.idservicio,
                            tipo_usuario.idtipousuario,
                            servicio_data['duracion'],
                            Decimal(str(servicio_data['costo']))
                        ])
                    servicios_nombres.append(servicio.descripcion)
                except ObjectDoesNotExist as e:
                    # Si no se encuentra el servicio o el tipo de usuario, eliminamos la cita y lanzamos un error
                    cita.delete()
                    logger.error(f"Error al crear servicio para cita: {str(e)}")
                    return JsonResponse({'success': False, 'error': f'Error: {str(e)}. Por favor, verifique los datos del servicio y del empleado.'})
        
        # Enviar notificación por WhatsApp
        mensaje = f"Hola {cliente.nombre}, su cita en la peluquería ha sido agendada para el {fecha_hora_inicio.strftime('%d/%m/%Y')} a las {fecha_hora_inicio.strftime('%H:%M')}. "
        mensaje += f"Servicios: {', '.join(servicios_nombres)}. "
        mensaje += f"Duración total: {duracion_total} minutos. Precio total: ${cita.precio_total}. ¡Le esperamos!"

        logger.info(f"Intentando enviar mensaje a: {cliente.telefono}")
        if whatsapp_service.enviar_mensaje(cliente.telefono, mensaje):
            logger.info("Mensaje de WhatsApp enviado con éxito")
            return JsonResponse({'success': True, 'message': 'Cita agendada con éxito y notificación enviada'})
        else:
            logger.warning(f"No se pudo enviar el mensaje de WhatsApp a {cliente.telefono}")
            return JsonResponse({'success': True, 'message': 'Cita agendada con éxito, pero hubo un problema al enviar la notificación'})
    
    except json.JSONDecodeError as e:
        logger.error(f"Error en el formato JSON: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error en el formato JSON: {str(e)}'})
    except Exception as e:
        logger.error(f"Error inesperado al agendar cita: {str(e)}")
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
    
@csrf_exempt
@require_http_methods(["POST"])
def editar_cita(request):
    try:
        data = json.loads(request.body)
        cita_id = data.get('cita_id')
        
        with transaction.atomic():
            # Obtener la cita existente
            cita = Cita.objects.get(idcita=cita_id)
            
            # Actualizar los campos de la cita
            cita.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            cita.hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            cita.estado = data['estado']
            cita.tiempo_gracia = data['tiempo_gracia']
            
            # Calcular la hora de fin y el precio total
            duracion_total = timedelta(minutes=sum(servicio['duracion'] for servicio in data['servicios']))
            cita.hora_fin = (datetime.combine(datetime.min, cita.hora_inicio) + duracion_total).time()
            cita.precio_total = sum(servicio['precio'] for servicio in data['servicios'])
            
            cita.save()
            
            # Eliminar los servicios antiguos asociados a esta cita
            CitaServicio.objects.filter(idcita=cita).delete()
            
            # Crear nuevos registros de CitaServicio
            for servicio_data in data['servicios']:
                servicio = Servicio.objects.get(idservicio=servicio_data['idservicio'])
                tipo_usuario = TipoUsuario.objects.get(idtipousuario=servicio_data['idtipo_usuario'])
                CitaServicio.objects.create(
                    idcita=cita,
                    idservicio=servicio,
                    idtipo_usuario=tipo_usuario
                )
        
        return JsonResponse({'success': True, 'message': 'Cita actualizada correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al actualizar la cita: {str(e)}'}, status=400)
    

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def confirmar_cita(request):
    try:
        data = json.loads(request.body)
        idcita = data.get('id_cita')
        
        if not idcita:
            return JsonResponse({'success': False, 'message': 'ID de cita no proporcionado'}, status=400)
        
        cita = Cita.objects.get(idcita=idcita)
        cita.estado = 'pendiente'
        cita.save()
        
        # Preparar mensaje de WhatsApp
        mensaje = f"Hola {cita.idcliente.nombre}, su cita para el {cita.fecha.strftime('%d/%m/%Y')} "
        mensaje += f"a las {cita.hora_inicio.strftime('%H:%M')} ha sido confirmada. "
        mensaje += "Por favor, asegúrese de llegar a tiempo. ¡Le esperamos!"
        
        # Enviar mensaje de WhatsApp
        if whatsapp_service.enviar_mensaje(cita.idcliente.telefono, mensaje):
            return JsonResponse({
                'success': True, 
                'message': 'Cita confirmada y notificación enviada',
                'whatsapp_message': mensaje
            })
        else:
            return JsonResponse({
                'success': True, 
                'message': 'Cita confirmada, pero hubo un problema al enviar la notificación',
                'whatsapp_message': mensaje
            })
    
    except Cita.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'La cita no existe'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al confirmar la cita: {str(e)}'}, status=500)

def eliminar_cita(request):
    try:
        data = json.loads(request.body)
        idcita = data.get('id_cita')
        
        if not idcita:
            return JsonResponse({'success': False, 'message': 'ID de cita no proporcionado'}, status=400)

        with connection.cursor() as cursor:
            # Obtener información de la cita antes de eliminarla
            cursor.execute("""
                SELECT c.fecha, c.hora_inicio, cl.nombre, cl.apellido, cl.telefono,
                       array_agg(s.descripcion) as servicios,
                       SUM(cs.duracion) as duracion_total,
                       c.es_agendada
                FROM citas c
                JOIN cliente cl ON c.idcliente = cl.cedula
                LEFT JOIN cita_servicios cs ON c.idcita = cs.idcita
                LEFT JOIN servicios s ON cs.idservicio = s.idservicio
                WHERE c.idcita = %s
                GROUP BY c.idcita, c.fecha, c.hora_inicio, cl.nombre, cl.apellido, cl.telefono, c.es_agendada
            """, [idcita])
            
            cita_info = cursor.fetchone()
            
            if not cita_info:
                return JsonResponse({'success': False, 'message': 'La cita no existe'}, status=404)
            
            fecha, hora_inicio, nombre, apellido, telefono, servicios, duracion_total, es_agendada = cita_info
            
            # Eliminar la cita y sus servicios asociados
            with transaction.atomic():
                cursor.execute("DELETE FROM cita_servicios WHERE idcita = %s", [idcita])
                cursor.execute("DELETE FROM citas WHERE idcita = %s", [idcita])

        # Si la cita no fue agendada, no enviamos mensaje de WhatsApp
        if not es_agendada:
            logger.info(f"Cita no agendada eliminada. No se envía notificación.")
            return JsonResponse({'success': True, 'message': 'Cita no agendada eliminada sin notificación'})

        # Si la cita fue agendada, procedemos con la notificación
        fecha_formateada = fecha.strftime('%d/%m/%Y')
        hora_inicio_formateada = hora_inicio.strftime('%H:%M')
        servicios_descripciones = ', '.join(filter(None, servicios))

        mensaje = f"Hola {nombre} {apellido}, su cita del {fecha_formateada} a las {hora_inicio_formateada} ha sido cancelada. "
        mensaje += f"Servicios cancelados: {servicios_descripciones}. "
        mensaje += f"Duración total cancelada: {duracion_total} minutos. "
        mensaje += "Si tiene alguna pregunta, por favor contáctenos."

        logger.info(f"Intentando enviar mensaje de cancelación a: {telefono}")
        if whatsapp_service.enviar_mensaje(telefono, mensaje):
            logger.info("Mensaje de WhatsApp de cancelación enviado con éxito")
            return JsonResponse({'success': True, 'message': 'Cita eliminada y notificación enviada'})
        else:
            logger.warning(f"No se pudo enviar el mensaje de WhatsApp de cancelación a {telefono}")
            return JsonResponse({'success': True, 'message': 'Cita eliminada, pero hubo un problema al enviar la notificación'})

    except json.JSONDecodeError as e:
        logger.error(f"Error en el formato JSON: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error en el formato JSON: {str(e)}'})
    except Exception as e:
        logger.error(f"Error inesperado al eliminar cita: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)