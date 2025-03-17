from django.urls import path
from chats_app import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:sender_id>/<int:receiver_id>/', consumers.ChatConsumer.as_asgi()),
    path('group_chat/<int:group_id>/',consumers.GroupConsumer.as_asgi()),
    path('user-online-status/<int:user_id>/',consumers.UserStatus.as_asgi()),
    path('notifications/<int:user_id>/',consumers.Notifications.as_asgi())
]
