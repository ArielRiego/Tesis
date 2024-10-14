import os
import django
import sys

# Obtener la ruta absoluta del directorio actual (donde está manage.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Añadir el directorio actual al sys.path
sys.path.append(BASE_DIR)

# Configurar el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Peluqueria.settings")
django.setup()

# Ahora importamos los modelos
from usuarios.models import Usuario, TipoUsuario, UsuarioTipoUsuario
from django.db import transaction, connection

def crear_usuario(username, mail, nombre, apellido, password, tipo_usuario):
    try:
        with transaction.atomic():
            # Crear el usuario
            usuario = Usuario.objects.create_user(
                username=username,
                mail=mail,
                nombre=nombre,
                apellido=apellido,
                password=password
            )
            
            # Obtener el tipo de usuario
            tipo = TipoUsuario.objects.get(descripcion=tipo_usuario)
            
            # Crear la relación usuario-tipo de usuario usando SQL directo
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO usuario_tipo_usuario (idusuario, idtipousuario) VALUES (%s, %s)",
                    [usuario.idusuario, tipo.idtipousuario]
                )
            
            print(f"Usuario {username} creado exitosamente con rol {tipo_usuario}")
    except Exception as e:
        print(f"Error al crear el usuario: {str(e)}")

# Ejemplo de uso
crear_usuario("peluquero", "peluquero@example.com", "Nombre1", "Apellido1", "123", "peluquero")
crear_usuario("manicurista", "manicurista@example.com", "Nombre1", "Apellido1", "123", "manicurista")
crear_usuario("estilista", "estilista@example.com", "Nombre1", "Apellido1", "123", "estilista")
crear_usuario("pedicurista", "pedicurista@example.com", "Nombre1", "Apellido1", "123", "pedicurista")
crear_usuario("maquilladora", "maquilladora@example.com", "Nombre1", "Apellido1", "123", "maquilladora")
crear_usuario("recepcionista", "recepcionista@example.com", "Nombre1", "Apellido1", "123", "recepcionista")
crear_usuario("practicante", "practicante@example.com", "Nombre1", "Apellido1", "123", "practicante")







