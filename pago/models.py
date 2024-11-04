from django.db import models
from django.utils import timezone

class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        # Add more payment methods as needed
    ]

    ESTADO_CHOICES = [
        ('completado', 'Completado'),
        ('pendiente', 'Pendiente'),
        ('cancelado', 'Cancelado'),
        # Add more status options as needed
    ]

    idpago = models.AutoField(primary_key=True)
    idcita = models.ForeignKey('agendamiento.Cita', on_delete=models.CASCADE, db_column='idcita')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    fecha_pago = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completado')
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comprobante_emitido = models.BooleanField(default=False)
    idusuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, db_column='idusuario')
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Esto evita que Django intente crear o modificar la tabla
        db_table = 'pagos'
        indexes = [
            models.Index(fields=['idcita'], name='idx_pagos_idcita'),
        ]

    def __str__(self):
        return f"Pago {self.idpago} - Cita {self.idcita_id} - Monto: {self.monto}"

    def save(self, *args, **kwargs):
        # Update the updated_at field on each save
        self.updated_at = timezone.now()
        super(Pago, self).save(*args, **kwargs)