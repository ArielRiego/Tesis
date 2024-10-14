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

    class Meta:
        managed = False  # Esto evita que Django intente crear o modificar la tabla
        db_table = 'citas'

    def __str__(self):
        return f"Cita {self.idcita} - {self.fecha} {self.hora_inicio} - Cliente: {self.idcliente.nombre} {self.idcliente.apellido}"


class CitaServicio(models.Model):
    idcita = models.ForeignKey(Cita, on_delete=models.CASCADE)
    idservicio = models.ForeignKey('servicios.Servicio', on_delete=models.CASCADE)
    idtipo_usuario = models.ForeignKey('usuarios.TipoUsuario', on_delete=models.CASCADE)
    duracion = models.IntegerField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = True if 'test' in sys.argv else False
        db_table = 'cita_servicios'

class CitaRecurrente(models.Model):
    PATRON_CHOICES = [
        ('DIARIO', 'Diario'),
        ('SEMANAL', 'Semanal'),
        ('MENSUAL', 'Mensual'),
    ]

    idcita = models.ForeignKey(Cita, on_delete=models.CASCADE)
    patron_recurrencia = models.CharField(max_length=50, choices=PATRON_CHOICES)
    intervalo = models.IntegerField()
    dia_semana = models.IntegerField(null=True, blank=True)
    dia_mes = models.IntegerField(null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        managed = True if 'test' in sys.argv else False
        db_table = 'citas_recurrentes'

    def generar_citas(self):
        if self.patron_recurrencia == 'DIARIO':
            freq = DAILY
        elif self.patron_recurrencia == 'SEMANAL':
            freq = WEEKLY
        elif self.patron_recurrencia == 'MENSUAL':
            freq = MONTHLY

        cita_base = self.idcita
        for fecha in rrule(freq, dtstart=self.fecha_inicio, until=self.fecha_fin, interval=self.intervalo):
            if self.patron_recurrencia == 'SEMANAL' and fecha.weekday() != self.dia_semana:
                continue
            if self.patron_recurrencia == 'MENSUAL' and fecha.day != self.dia_mes:
                continue

            nueva_cita = Cita.objects.create(
                idcliente=cita_base.idcliente,
                idusuario=cita_base.idusuario,
                fecha=fecha.date(),
                hora_inicio=cita_base.hora_inicio,
                hora_fin=cita_base.hora_fin,
                estado='PROGRAMADO',
                tiempo_gracia=cita_base.tiempo_gracia,
                precio_total=cita_base.precio_total,
                observaciones=cita_base.observaciones
            )

            for servicio in CitaServicio.objects.filter(idcita=cita_base):
                CitaServicio.objects.create(
                    idcita=nueva_cita,
                    idservicio=servicio.idservicio,
                    idtipo_usuario=servicio.idtipo_usuario,
                    duracion=servicio.duracion,
                    costo=servicio.costo
                )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.generar_citas()