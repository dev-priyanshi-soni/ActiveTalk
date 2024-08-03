from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="home"),
    path('chats_page/<int:id>/', views.chats_page, name='chats_page'),
    path('get_previous_messages/<int:sender_id>/<int:receiver_id>/<int:page>/', views.get_previous_messages, name='get_previous_messages'),
    path('reply_to_message/<int:sender_id>/<int:receiver_id>/<int:message_id>/', views.reply_to_message, name='reply_to_message'),
]