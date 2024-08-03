from django.urls import path
from chats_app import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:sender_id>/<int:receiver_id>/', consumers.ChatConsumer.as_asgi()),
]