import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_application.settings")

import django
django.setup()

from django.core.management import call_command


from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

from chats_app import routing

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket":AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns))
    }
)
