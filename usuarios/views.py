# C:\Users\AGRA\Desktop\Tesis\Peluqueria\usuarios\views.py
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging

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

