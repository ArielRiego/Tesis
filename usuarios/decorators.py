from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def superuser_required(function=None, redirect_url='inicio'):
    def check_superuser(user):
        if user.is_authenticated and user.usuario_administrador:
            return True
        return False

    actual_decorator = user_passes_test(
        check_superuser,
        login_url=redirect_url,
        redirect_field_name=REDIRECT_FIELD_NAME
    )

    if function:
        return actual_decorator(function)
    return actual_decorator

def estilista_forbidden(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.tiene_rol('estilista'):
                return function(request, *args, **kwargs)
            else:
                messages.error(request, 'No tienes permiso para acceder a esta página.')
                return redirect('inicio')
        else:
            return redirect('login')
    return wrap