from django.contrib.auth.models import User

# Busca al usuario por nombre de usuario
user = User.objects.get(username='ari')
print(user)  # Debe mostrar el usuario 'ari'

# Verifica si la contraseña es correcta
is_correct = user.check_password('123')
print(is_correct)  # Debe devolver True si la contraseña es correcta
