from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import sys 

class TipoUsuario(models.Model):
    idtipousuario = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField()

    class Meta:
        db_table = 'tipo_usuario'
        #managed = False  # Django no gestionará las migraciones para esta tabla
        managed = True if 'test' in sys.argv else False
    def __str__(self):
        return self.descripcion

class UsuarioManager(BaseUserManager):
    def create_user(self, username, mail, nombre, apellido, idtipousuario, password=None):
        if not mail:
            raise ValueError('El usuario debe tener un correo electrónico')
        if not username:
            raise ValueError('El usuario debe tener un nombre de usuario')
        

         # Convertir idtipousuario a una instancia de TipoUsuario
        tipo_usuario = TipoUsuario.objects.get(pk=idtipousuario)

        usuario = self.model(
            username=username,
            mail=self.normalize_email(mail),
            nombre=nombre,
            apellido=apellido,
            idtipousuario=tipo_usuario,
        )
        
        usuario.set_password(password)
        usuario.save()
        return usuario

    def create_superuser(self, username, mail, nombre, apellido, idtipousuario, password=None):
        usuario = self.create_user(
            username=username,
            mail=mail,
            nombre=nombre,
            apellido=apellido,
            idtipousuario=idtipousuario,
            password=password,
        )
        usuario.usuario_administrador = True
        usuario.save()
        return usuario

class Usuario(AbstractBaseUser):

    idusuario = models.AutoField(primary_key=True)
    idtipousuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE, db_column='idtipousuario')
    username = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    nombre = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    apellido = models.CharField(max_length=50)
    fechacreacion = models.DateTimeField(auto_now_add=True)
    mail = models.EmailField(max_length=255, unique=True)
    usuario_administrador = models.BooleanField(default=False)
    last_login = None
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['mail', 'nombre', 'apellido', 'idtipousuario']
   

    class Meta:
        db_table = 'usuario'
        #managed = False  # Django no gestionará las migraciones para esta tabla
        managed = True if 'test' in sys.argv else False
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.usuario_administrador
