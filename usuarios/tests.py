from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import TipoUsuario

class UsuarioTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.tipo_usuario = TipoUsuario.objects.create(descripcion='Test', activo=True)

    def test_crear_usuario(self):
        try:
            usuario = self.User.objects.create_user(
                username='testuser',
                mail='test@example.com',
                nombre='Test',
                apellido='User',
                idtipousuario=self.tipo_usuario.idtipousuario,
                password='testpass123'
            )
            print(f"\nUsuario '{usuario.username}' creado exitosamente.")
            self.assertEqual(usuario.username, 'testuser')
            self.assertEqual(usuario.mail, 'test@example.com')
            self.assertTrue(usuario.check_password('testpass123'))
            self.assertEqual(usuario.idtipousuario, self.tipo_usuario)
        except Exception as e:
            print(f"\nError al crear usuario: {str(e)}")
            self.fail("La creación del usuario falló.")

    def test_crear_usuario_sin_username(self):
        try:
            self.User.objects.create_user(
                username='',
                mail='test@example.com',
                nombre='Test',
                apellido='User',
                idtipousuario=self.tipo_usuario.idtipousuario,
                password='testpass123'
            )
            self.fail("Se creó un usuario sin username, lo cual no debería ser posible.")
        except ValueError as e:
            print(f"\nUsuario no creado: {str(e)}")
            # La prueba pasa si se lanza una excepción

    def test_crear_usuario_sin_email(self):
        try:
            self.User.objects.create_user(
                username='testuser2',
                mail='',
                nombre='Test',
                apellido='User',
                idtipousuario=self.tipo_usuario.idtipousuario,
                password='testpass123'
            )
            self.fail("Se creó un usuario sin email, lo cual no debería ser posible.")
        except ValueError as e:
            print(f"\nUsuario no creado: {str(e)}")
            # La prueba pasa si se lanza una excepción