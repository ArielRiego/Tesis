from django.test import TestCase, Client
from django.urls import reverse
from .models import Cliente

class ClienteModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            cedula=1234567,
            nombre="Juan",
            apellido="Pérez",
            email="juan@example.com",
            ruc="1234567-1",
            telefono="0991234567"
        )

    def test_cliente_creation(self):
        self.assertEqual(self.cliente.cedula, 1234567)
        self.assertEqual(self.cliente.nombre, "Juan")
        self.assertEqual(self.cliente.apellido, "Pérez")
        self.assertEqual(self.cliente.email, "juan@example.com")
        self.assertEqual(self.cliente.ruc, "1234567-1")
        self.assertEqual(self.cliente.telefono, "0991234567")

    def test_cliente_str(self):
        self.assertEqual(str(self.cliente), "Juan Pérez")

class ClienteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(
            cedula=1234567,
            nombre="Juan",
            apellido="Pérez",
            email="juan@example.com",
            ruc="1234567-1",
            telefono="0991234567"
        )

    def test_agregar_cliente(self):
        response = self.client.post(reverse('agregar_cliente'), {
            'cedula': 7654321,
            'nombre': 'María',
            'apellido': 'González',
            'email': 'maria@example.com',
            'ruc': '7654321-1',
            'telefono': '0997654321'
        })
        self.assertEqual(response.status_code, 302)  # Redirección después de agregar
        self.assertTrue(Cliente.objects.filter(cedula=7654321).exists())
        print("Test agregar_cliente completado.")

    def test_listar_clientes(self):
        
        # Crear algunos clientes adicionales para la prueba
        Cliente.objects.create(cedula=2345678, nombre="María", apellido="González", email="maria@example.com", ruc="2345678-1", telefono="0992345678")
        ultimo_cliente = Cliente.objects.create(cedula=3456789, nombre="Carlos", apellido="Rodríguez", email="carlos@example.com", ruc="3456789-1", telefono="0993456789")

        # Obtener todos los clientes de la base de datos
        clientes = Cliente.objects.all()

        print("\nClientes en la base de datos:")
        for cliente in clientes:
            print(f"- {cliente.nombre} {cliente.apellido} (Cédula: {cliente.cedula})")

        # Realizar la solicitud GET a la vista de listar clientes
        response = self.client.get(reverse('listar_clientes'))

        # Verificar que la respuesta sea exitosa (código 200)
        self.assertEqual(response.status_code, 200)

        # Verificar que la respuesta contenga el nombre y apellido del último cliente agregado
        self.assertContains(response, ultimo_cliente.nombre)
        self.assertContains(response, ultimo_cliente.apellido)

        # Verificar que todos los clientes estén en la respuesta
        for cliente in clientes:
            self.assertContains(response, cliente.nombre)
            self.assertContains(response, cliente.apellido)

        print("Test listar_clientes completado.")
    def test_editar_cliente(self):
        response = self.client.post(reverse('editar_cliente', args=[self.cliente.cedula]), {
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez',
            'email': 'juancarlos@example.com',
            'ruc': '1234567-1',
            'telefono': '0991234567'
        })
        self.assertEqual(response.status_code, 302)  # Redirección después de editar
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Juan Carlos')
        print("Test editar_cliente completado.")

    def test_eliminar_cliente(self):
        response = self.client.post(reverse('eliminar_cliente', args=[self.cliente.cedula]))
        self.assertEqual(response.status_code, 302)  # Redirección después de eliminar
        self.assertFalse(Cliente.objects.filter(cedula=self.cliente.cedula).exists())
        print("Test eliminar_cliente completado.")

print("Iniciando pruebas para la aplicación de clientes...")