from twilio.rest import Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def enviar_mensaje(self, numero_destino, mensaje):
        # Asegurar que el número esté en el formato correcto
        if numero_destino.startswith('0'):
            numero_destino = '595' + numero_destino[1:]
        elif not numero_destino.startswith('595'):
            numero_destino = '595' + numero_destino

        try:
            message = self.client.messages.create(
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                body=mensaje,
                to=f'whatsapp:+{numero_destino}'
            )
            logger.info(f"Mensaje enviado: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar mensaje: {str(e)}")
            return False

whatsapp_service = WhatsAppService()