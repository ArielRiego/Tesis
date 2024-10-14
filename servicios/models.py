from django.db import models
from usuarios.models import TipoUsuario 
import sys

class Servicio(models.Model):
    idservicio = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    duracion = models.IntegerField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    tipos_usuario = models.ManyToManyField(TipoUsuario, through='ServicioTipoUsuario')

    class Meta:
        db_table = 'servicios'
        managed = True if 'test' in sys.argv else False

    def __str__(self):
        return self.descripcion

class ServicioTipoUsuario(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, db_column='idservicio')
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE, db_column='idtipousuario')

    class Meta:
        db_table = 'servicio_tipo_usuario'
        unique_together = ('servicio', 'tipo_usuario')
        managed = False

    def __str__(self):
        return f"{self.servicio.descripcion} - {self.tipo_usuario.descripcion}"