from django.urls import path
from chats_app import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:sender_id>/<int:receiver_id>/', consumers.ChatConsumer.as_asgi()),
    path('group_chat/<int:group_id>/',consumers.GroupConsumer.as_asgi())
]