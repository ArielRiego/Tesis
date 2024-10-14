# C:\Users\AGRA\Desktop\Tesis\Peluqueria\usuarios\views.py
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
import logging
from django.db.models import Q
from django.db import transaction
from .models import Usuario, TipoUsuario, UsuarioTipoUsuario
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, connection
from .models import Usuario, TipoUsuario
from .decorators import superuser_required


logger = logging.getLogger(__name__)

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso')
            return redirect('/menu/')
        else:
            # Depuración adicional
            logger.debug("Formulario no válido: %s", form.errors)
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
    else:
        form = AuthenticationForm()  # Si el método no es POST, se inicializa el formulario vacío

    return render(request, 'login.html', {'form': form})


def inicio_view(request):
    return render(request, 'index.html')

@login_required
def menu_view(request):
    return render(request, 'menu.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from .models import Usuario, TipoUsuario, UsuarioTipoUsuario

def es_superusuario(user):
    return user.is_authenticated and user.usuario_administrador

def superuser_required(view_func):
    decorated_view_func = user_passes_test(es_superusuario, login_url='acceso_denegado')(view_func)
    return login_required(decorated_view_func)

@login_required
@superuser_required
def agregar_empleado(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        mail = request.POST.get('mail')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        password = request.POST.get('password')
        tipo_usuario = request.POST.get('tipo_usuario')

        try:
            with transaction.atomic():
                # Verificar si el usuario ya existe
                if Usuario.objects.filter(username=username).exists():
                    raise ValueError("El nombre de usuario ya está en uso.")
                
                if Usuario.objects.filter(mail=mail).exists():
                    raise ValueError("El correo electrónico ya está en uso.")

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
                
                messages.success(request, f'Empleado {username} creado exitosamente con rol {tipo_usuario}')
                return redirect('listar_empleados')
        except ValueError as e:
            messages.error(request, str(e))
        except TipoUsuario.DoesNotExist:
            messages.error(request, "El tipo de usuario seleccionado no existe.")
        except Exception as e:
            messages.error(request, f'Error al crear el empleado: {str(e)}')

    # Si es GET o si hubo un error en POST, mostrar el formulario
    tipos_usuario = TipoUsuario.objects.all()
    return render(request, 'menu_agregar_empleado.html', {'tipos_usuario': tipos_usuario})

@login_required
@superuser_required
def listar_empleados(request):
    query = request.GET.get('q', '')
    if query:
        empleados = Usuario.objects.filter(
            Q(username__icontains=query) |
            Q(mail__icontains=query) |
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query)
        ).exclude(usuario_administrador=True)
    else:
        empleados = Usuario.objects.exclude(usuario_administrador=True)
    
    return render(request, 'menu_empleados.html', {
        'empleados': empleados, 
        'query': query,
    })

@login_required
@superuser_required
def editar_empleado(request, idusuario):
    usuario = get_object_or_404(Usuario, idusuario=idusuario)
    tipos_usuario = TipoUsuario.objects.all()
    
    # Obtener el tipo de usuario actual usando SQL directo
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tu.descripcion FROM usuario_tipo_usuario utu "
            "JOIN tipo_usuario tu ON utu.idtipousuario = tu.idtipousuario "
            "WHERE utu.idusuario = %s",
            [usuario.idusuario]
        )
        resultado = cursor.fetchone()
        tipo_actual = resultado[0] if resultado else None

    if request.method == 'POST':
        username = request.POST.get('username')
        mail = request.POST.get('mail')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        new_password = request.POST.get('password')
        tipo_usuario = request.POST.get('tipo_usuario')

        try:
            with transaction.atomic():
                # Actualizar datos básicos del usuario
                usuario.username = username
                usuario.mail = mail
                usuario.nombre = nombre
                usuario.apellido = apellido

                # Cambiar la contraseña si se proporciona una nueva
                if new_password:
                    usuario.set_password(new_password)

                usuario.save()

                # Actualizar el tipo de usuario
                nuevo_tipo = TipoUsuario.objects.get(descripcion=tipo_usuario)
                
                # Eliminar la relación anterior y crear la nueva usando SQL directo
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM usuario_tipo_usuario WHERE idusuario = %s",
                        [usuario.idusuario]
                    )
                    cursor.execute(
                        "INSERT INTO usuario_tipo_usuario (idusuario, idtipousuario) VALUES (%s, %s)",
                        [usuario.idusuario, nuevo_tipo.idtipousuario]
                    )

                messages.success(request, f'Empleado {username} actualizado exitosamente')
                return redirect('listar_empleados')
        except Exception as e:
            messages.error(request, f'Error al actualizar el empleado: {str(e)}')

    context = {
        'usuario': usuario,
        'tipos_usuario': tipos_usuario,
        'tipo_actual': tipo_actual
    }
    return render(request, 'menu_editar_empleado.html', context)




@login_required
@superuser_required

def eliminar_empleado(request, idusuario):
    usuario = get_object_or_404(Usuario, idusuario=idusuario)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Eliminar las relaciones en la tabla usuario_tipo_usuario
                UsuarioTipoUsuario.objects.filter(usuario=usuario).delete()
                
                # Eliminar el usuario
                usuario.delete()
                
                messages.success(request, f'Usuario {usuario.username} eliminado exitosamente')
            return redirect('listar_empleados')
        except Exception as e:
            messages.error(request, f'Error al eliminar el usuario: {str(e)}')
    
    return render(request, 'menu_eliminar_empleado.html', {'usuario': usuario})


@login_required
def acceso_denegado(request):
    user = request.user
    context = {
        'user_name': user.username,
        'user_email': user.mail,
        'user_role': 'Administrador' if user.usuario_administrador else 'Usuario Regular'
    }
    return render(request, 'acceso_denegado.html', context)