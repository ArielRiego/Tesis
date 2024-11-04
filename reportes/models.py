# En models.py
from django.db import models

class ReportesAgregados(models.Model):
    tipo_reporte = models.CharField(max_length=50)
    fecha = models.DateField()
    datos = models.JSONField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Esto evita que Django intente crear o modificar la tabla
        db_table = 'reportes_agregados'
        unique_together = ('tipo_reporte', 'fecha')