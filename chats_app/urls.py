from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="home"),
    path('chats_page/<int:id>/', views.chats_page, name='chats_page'),
    path('get_previous_messages/<int:sender_id>/<int:receiver_id>/<int:page>/', views.get_previous_messages, name='get_previous_messages'),
    path('reply_to_message/<int:sender_id>/<int:receiver_id>/<int:message_id>/', views.reply_to_message, name='reply_to_message'),
    path('join_group/<int:group_id>/',views.join_group,name='join_group'),
    path('create_group/',views.create_group,name='create_group'),
    path('group_chat/<int:group_id>/',views.group_chat,name='group_chat'),
    path('get_previous_group_chats_messages/<int:group_id>/<int:page>/<int:last_message_id>/',views.get_previous_group_chats_messages,name='get_previous_group_chats_messages'),
    path('get_next_group_chats_messages/<int:group_id>/<int:page>/<int:curr_msg_id>/',views.get_next_group_chats_messages,name='get_next_group_chats_messages'),
    path('get_read_statuses/<int:group_id>/<int:message_id>/',views.get_read_statuses,name='get_read_statuses'),
    path('get_group_members/<int:group_id>/',views.get_group_members,name='get_group_members'),
    path('remove_group_member/<int:group_id>/<int:group_member_id>/',views.remove_group_member,name='remove_group_member')
]