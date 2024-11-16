from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import sys

class TipoUsuario(models.Model):
    ESTILISTA = 'estilista'
    MANICURISTA = 'manicurista'
    PEDICURISTA = 'pedicurista'
    MAQUILLADORA = 'maquilladora'
    RECEPCIONISTA = 'recepcionista'
    PRACTICANTE = 'practicante'

    TIPO_CHOICES = [
        (ESTILISTA, 'Estilista'),
        (MANICURISTA, 'Manicurista'),
        (PEDICURISTA, 'Pedicurista'),
        (MAQUILLADORA, 'Maquilladora'),
        (RECEPCIONISTA, 'Recepcionista'),
        (PRACTICANTE, 'Practicante'),
    ]

    idtipousuario = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100, choices=TIPO_CHOICES, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'tipo_usuario'
        managed = True if 'test' in sys.argv else False

    def __str__(self):
        return self.descripcion

class UsuarioManager(BaseUserManager):
    def create_user(self, username, mail, nombre, apellido, password=None, **extra_fields):
        if not mail:
            raise ValueError('El usuario debe tener un correo electrónico')
        if not username:
            raise ValueError('El usuario debe tener un nombre de usuario')

        usuario = self.model(
            username=username,
            mail=self.normalize_email(mail),
            nombre=nombre,
            apellido=apellido,
            **extra_fields
        )
        
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username, mail, nombre, apellido, password=None):
        usuario = self.create_user(
            username=username,
            mail=mail,
            nombre=nombre,
            apellido=apellido,
            password=password,
        )
        usuario.usuario_administrador = True
        usuario.is_staff = True
        usuario.save(using=self._db)
        return usuario

class Usuario(AbstractBaseUser):
    last_login = None
    idusuario = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    fechacreacion = models.DateTimeField(auto_now_add=True)
    mail = models.EmailField(max_length=255, unique=True)
    usuario_administrador = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    tipos_usuario = models.ManyToManyField(TipoUsuario, through='UsuarioTipoUsuario')

    objects = UsuarioManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['mail', 'nombre', 'apellido']

    class Meta:
        db_table = 'usuario'
        managed = True if 'test' in sys.argv else False

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def has_perm(self, perm, obj=None):
        return self.usuario_administrador

    def has_module_perms(self, app_label):
        return self.usuario_administrador

    @property
    def is_superuser(self):
        return self.usuario_administrador

    @property
    def is_active(self):
        return self.activo

    def tiene_rol(self, rol):
        return self.tipos_usuario.filter(descripcion=rol).exists()

class UsuarioTipoUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idusuario', primary_key=True)
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE, db_column='idtipousuario')

    class Meta:
        db_table = 'usuario_tipo_usuario'
        unique_together = ('usuario', 'tipo_usuario')
        managed = False

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_usuario.descripcion}"

class HorarioTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idusuario')
    dia_semana = models.IntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = 'horario_trabajo'
        managed = True if 'test' in sys.argv else False

    def __str__(self):
        return f"{self.usuario.username} - Día {self.dia_semana}: {self.hora_inicio} - {self.hora_fin}"

class TipoPermiso(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'tipo_permiso'
        managed = True if 'test' in sys.argv else False

    def __str__(self):
        return self.nombre

class Ausencia(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idusuario')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    motivo = models.CharField(max_length=255, null=True, blank=True)
    id_tipo_permiso = models.ForeignKey(TipoPermiso, on_delete=models.SET_NULL, null=True, db_column='id_tipo_permiso')
    aprobado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='ausencias_aprobadas', db_column='aprobado_por')
    aprobado = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'ausencias'
        managed = True if 'test' in sys.argv else False

    def __str__(self):
        return f"{self.usuario.username} - {self.id_tipo_permiso} ({self.fecha_inicio} a {self.fecha_fin})"