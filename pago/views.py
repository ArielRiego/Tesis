from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Pago
from agendamiento.models import Cita, CitaServicio
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from decimal import Decimal
import logging
from django.db.models import Q
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from agendamiento.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

@login_required
def menu_pago(request):
    idcita = request.GET.get('idcita')
    if idcita:
        # Si se proporciona un ID de cita, pre-cargar esa cita
        cita = get_object_or_404(Cita, idcita=idcita)
        context = {'cita_preseleccionada': cita}
    else:
        # Si no, mostrar todas las citas pendientes
        context = {}
    return render(request, 'menu_pago.html', context)



@login_required
def citas_pendientes(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.idcita, c.fecha, c.hora_inicio, cl.nombre, cl.apellido, 
                   array_agg(s.descripcion) as servicios
            FROM citas c
            JOIN cliente cl ON c.idcliente = cl.cedula
            LEFT JOIN cita_servicios cs ON c.idcita = cs.idcita
            LEFT JOIN servicios s ON cs.idservicio = s.idservicio
            WHERE LOWER(c.estado) = 'pendiente'
            GROUP BY c.idcita, c.fecha, c.hora_inicio, cl.nombre, cl.apellido
            ORDER BY c.fecha, c.hora_inicio
        """)
        citas = cursor.fetchall()

    data = [{
        'idcita': cita[0],
        'fecha': cita[1].strftime('%Y-%m-%d'),
        'cliente': f"{cita[3]} {cita[4]}",
        'servicios': [{'nombre': servicio} for servicio in cita[5] if servicio]
    } for cita in citas]

    logger.debug(f"Número de citas pendientes encontradas: {len(data)}")
    logger.debug(f"Datos de citas pendientes: {data}")
    return JsonResponse(data, safe=False)

@login_required
def obtener_datos_cita(request, id_cita):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.idcita, c.fecha, c.hora_inicio, c.hora_fin, c.estado, c.tiempo_gracia, c.precio_total,
                   cl.cedula, cl.nombre, cl.apellido,
                   array_agg(DISTINCT jsonb_build_object(
                       'idservicio', s.idservicio,
                       'descripcion', s.descripcion,
                       'duracion', cs.duracion,
                       'costo', cs.costo,
                       'idtipo_usuario', tu.idtipousuario,
                       'nombre_empleado', u.nombre || ' ' || u.apellido,
                       'tipo_empleado', tu.descripcion
                   )) as servicios
            FROM citas c
            JOIN cliente cl ON c.idcliente = cl.cedula
            LEFT JOIN cita_servicios cs ON c.idcita = cs.idcita
            LEFT JOIN servicios s ON cs.idservicio = s.idservicio
            LEFT JOIN usuario_tipo_usuario utu ON cs.idtipo_usuario = utu.idtipousuario
            LEFT JOIN tipo_usuario tu ON utu.idtipousuario = tu.idtipousuario
            LEFT JOIN usuario u ON utu.idusuario = u.idusuario
            WHERE c.idcita = %s
            GROUP BY c.idcita, cl.cedula, cl.nombre, cl.apellido
        """, [id_cita])
        
        result = cursor.fetchone()

    if result is None:
        return JsonResponse({'error': 'Cita no encontrada'}, status=404)

    idcita, fecha, hora_inicio, hora_fin, estado, tiempo_gracia, precio_total, \
    cedula_cliente, nombre_cliente, apellido_cliente, servicios = result

    data = {
        'idcita': idcita,
        'fecha': fecha.strftime('%Y-%m-%d'),
        'hora_inicio': hora_inicio.strftime('%H:%M'),
        'hora_fin': hora_fin.strftime('%H:%M'),
        'estado': estado,
        'tiempo_gracia': tiempo_gracia,
        'precio_total': str(precio_total),
        'cliente': {
            'cedula': cedula_cliente,
            'nombre': nombre_cliente,
            'apellido': apellido_cliente
        },
        'servicios': servicios
    }

    return JsonResponse(data)

@login_required
@require_POST
@csrf_exempt
def procesar_pago(request):
    try:
        with transaction.atomic():
            data = json.loads(request.body)
            print("Datos recibidos:", data)

            idcita = data.get('idcita')
            monto = data.get('monto')
            metodo_pago = data.get('metodo_pago')
            descuento = data.get('descuento', 0)

            # Obtener la cita correspondiente
            try:
                cita = Cita.objects.get(idcita=idcita)
            except Cita.DoesNotExist:
                return JsonResponse({'success': False, 'mensaje': 'Cita no encontrada'}, status=404)

            # Obtener el usuario (asumiendo que tienes un usuario autenticado)
            # Si no tienes un usuario autenticado, necesitarás ajustar esta parte
            usuario = request.user if request.user.is_authenticated else None
            if not usuario:
                return JsonResponse({'success': False, 'mensaje': 'Usuario no autenticado'}, status=401)

            # Crear y guardar el pago
            pago = Pago(
                idcita_id=idcita,
                monto=Decimal(monto),
                metodo_pago=metodo_pago,
                descuento=Decimal(descuento),
                estado='completado',
                idusuario=usuario
            )
            pago.save()

            # Actualizar el estado de la cita a 'pagada' o el estado que corresponda
            cita.estado = 'pagada'
            cita.save()

            print(f"Pago guardado con ID: {pago.idpago}")
            # Obtener los servicios asociados a la cita usando SQL directo
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT s.descripcion, cs.duracion
                    FROM cita_servicios cs
                    JOIN servicios s ON cs.idservicio = s.idservicio    
                    WHERE cs.idcita = %s
                """, [idcita])
                servicios = cursor.fetchall()

            servicios_nombres = [servicio[0] for servicio in servicios]
            duracion_total = sum(servicio[1] for servicio in servicios)

            # Preparar el mensaje de WhatsApp
            cliente = cita.idcliente
            mensaje = f"Hola {cliente.nombre}, su pago ha sido procesado correctamente. "
            mensaje += f"Cita del {cita.fecha.strftime('%d/%m/%Y')} a las {cita.hora_inicio.strftime('%H:%M')}. "
            mensaje += f"Servicios: {', '.join(servicios_nombres)}. "
            mensaje += f"Duración total: {duracion_total} minutos. "
            mensaje += f"Monto pagado: ${monto} mediante {metodo_pago}. "
            if descuento > 0:
                mensaje += f"Descuento aplicado: ${descuento}. "
            mensaje += "¡Gracias por su preferencia!"

            # Enviar notificación por WhatsApp
            logger.info(f"Intentando enviar mensaje a: {cliente.telefono}")
            if whatsapp_service.enviar_mensaje(cliente.telefono, mensaje):
                logger.info("Mensaje de WhatsApp enviado con éxito")
                return JsonResponse({'success': True, 'mensaje': 'Pago procesado y guardado correctamente. Notificación enviada.'})
            else:
                logger.warning(f"No se pudo enviar el mensaje de WhatsApp a {cliente.telefono}")
                return JsonResponse({'success': True, 'mensaje': 'Pago procesado y guardado correctamente, pero hubo un problema al enviar la notificación.'})

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {str(e)}")
        return JsonResponse({'success': False, 'mensaje': 'Datos inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error al procesar el pago: {str(e)}")
        return JsonResponse({'success': False, 'mensaje': f'Error al procesar el pago: {str(e)}'}, status=500)

@login_required
def detalle_pago(request, idpago):
    pago = get_object_or_404(Pago, idpago=idpago)
    context = {
        'pago': pago,
        'cita': pago.idcita,
        'servicios': pago.idcita.citaservicio_set.all()
    }
    return render(request, 'pagos/detalle_pago.html', context)

@login_required
def editar_pago(request, idpago):
    pago = get_object_or_404(Pago, idpago=idpago)
    if request.method == 'POST':
        data = json.loads(request.body)
        pago.monto = Decimal(data['monto'])
        pago.metodo_pago = data['metodo_pago']
        pago.descuento = Decimal(data.get('descuento', '0'))
        pago.save()
        return JsonResponse({'success': True, 'mensaje': 'Pago actualizado exitosamente.'})
    else:
        context = {
            'pago': pago,
            'cita': pago.idcita,
            'servicios': pago.idcita.citaservicio_set.all()
        }
        return render(request, 'pagos/editar_pago.html', context)

@login_required
@require_POST
def eliminar_pago(request, idpago):
    pago = get_object_or_404(Pago, idpago=idpago)
    cita = pago.idcita
    cita.estado = 'Pendiente'
    cita.save()
    pago.delete()
    return JsonResponse({'success': True, 'mensaje': 'Pago eliminado exitosamente.'})

@login_required
def lista_pagos(request):
    pagos = Pago.objects.all().order_by('-fecha_pago')
    return render(request, 'pagos/lista_pagos.html', {'pagos': pagos})

@login_required
def obtener_datos_pago(request, idpago):
    pago = get_object_or_404(Pago, idpago=idpago)
    datos_pago = {
        'idpago': pago.idpago,
        'idcita': pago.idcita.idcita,
        'monto': float(pago.monto),
        'metodo_pago': pago.metodo_pago,
        'descuento': float(pago.descuento),
        'fecha_pago': pago.fecha_pago.strftime('%Y-%m-%d %H:%M:%S')
    }
    return JsonResponse(datos_pago)