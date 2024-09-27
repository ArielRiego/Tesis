from django.db import models

class Servicio(models.Model):
    idservicio = models.AutoField(primary_key=True)  # Django manejará el ID automáticamente
    descripcion = models.CharField(max_length=100)
    duracion = models.IntegerField()  # Cambiado a IntegerField si es duración en minutos
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'servicios'  # Nombre de la tabla en la base de datos

    def __str__(self):
        return self.descripcion
