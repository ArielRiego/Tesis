import sys
from django.db import models
from django.utils import timezone
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
from datetime import timedelta
from django.db import models
from cliente.models import Cliente

class Cita(models.Model):
    idcita = models.AutoField(primary_key=True)
    idcliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='idcliente', to_field='cedula')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20)
    tiempo_gracia = models.IntegerField()
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    es_agendada = models.BooleanField(default=True)  # Nuevo campo

    class Meta:
        managed = False  # Esto evita que Django intente crear o modificar la tabla
        db_table = 'citas'

    def __str__(self):
        return f"Cita {self.idcita} - {self.fecha} {self.hora_inicio} - Cliente: {self.idcliente.nombre} {self.idcliente.apellido}"


class CitaServicio(models.Model):
    idcita = models.ForeignKey(Cita, on_delete=models.CASCADE, db_column='idcita')
    idservicio = models.ForeignKey('servicios.Servicio', on_delete=models.CASCADE)
    idtipo_usuario = models.ForeignKey('usuarios.TipoUsuario', on_delete=models.CASCADE)
    duracion = models.IntegerField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = True if 'test' in sys.argv else False
        db_table = 'cita_servicios'
