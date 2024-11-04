from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse
from .models import ReportesAgregados
import json
from datetime import date, timedelta  # Añadimos esta importación
from django.db.models import Count, Sum
from django.utils import timezone
from agendamiento.models import CitaServicio
from servicios.models import Servicio

def obtener_reporte_servicios_populares(request):
    fecha_inicio = timezone.now().date() - timedelta(days=30)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.descripcion, COUNT(cs.idcita) as total_citas, SUM(cs.costo) as ingresos_totales
            FROM cita_servicios cs
            JOIN servicios s ON cs.idservicio = s.idservicio
            JOIN citas c ON cs.idcita = c.idcita
            WHERE c.fecha >= %s
            GROUP BY s.descripcion
            ORDER BY total_citas DESC
            LIMIT 5
        """, [fecha_inicio])
        
        servicios_populares = cursor.fetchall()

    labels = [servicio[0] for servicio in servicios_populares]
    data_citas = [servicio[1] for servicio in servicios_populares]
    data_ingresos = [float(servicio[2]) for servicio in servicios_populares]
    
    context = {
        'labels': json.dumps(labels),
        'data_citas': json.dumps(data_citas),
        'data_ingresos': json.dumps(data_ingresos),
        'ultima_actualizacion': timezone.now()
    }
    
    return render(request, 'menu_reportes.html', context)
def vista_reportes(request):
    # Obtén los datos de tu base de datos
    servicios_populares = [
        {'nombre': 'Corte de cabello', 'cantidad': 150},
        {'nombre': 'Tinte', 'cantidad': 80},
        # ... más servicios ...
    ]
    return render(request, 'tu_template.html', {'servicios_populares': servicios_populares})

def actualizar_reporte_servicios_populares():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT servicio.nombre, COUNT(*) as total
            FROM tu_app_cita cita
            JOIN tu_app_servicio servicio ON cita.servicio_id = servicio.id
            WHERE cita.fecha >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY servicio.nombre
            ORDER BY total DESC
            LIMIT 5
        """)
        resultados = cursor.fetchall()
    
    datos = json.dumps({row[0]: row[1] for row in resultados})
    
    ReportesAgregados.objects.update_or_create(
        tipo_reporte='servicios_populares',
        fecha=date.today(),
        defaults={'datos': datos}
    )
