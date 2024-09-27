from django.db import models

class Cliente(models.Model):
    cedula = models.IntegerField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)  
    ruc = models.CharField(max_length=15, unique=True) 
    telefono = models.CharField(max_length=20)
    historial = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"