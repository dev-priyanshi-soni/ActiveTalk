from django.contrib.auth.signals import user_logged_in,user_logged_out
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from auth_app.models import User 
from django.utils import timezone
from chats_app.models  import ChatModel
from django.db.models import Q
from .models import ActiveConversation


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    user.is_online=True
    user.save()
    broadcast_user_status(user.id, True)

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    user.is_online=False
    user.save()
    broadcast_user_status(user.id, False)

def broadcast_user_status(user_id, is_online):
    try:
        channel_layer = get_channel_layer()

        # chat_pairs = ChatModel.objects.filter(
        #     Q(sender_id=user_id) | Q(receiver_id=user_id),
        #     sent_time__gte=timezone.now() - timezone.timedelta(hours=12)
        # ).values_list('sender_id', 'receiver_id')
        # user_ids = {id for pair in chat_pairs for id in pair} - {user_id}

        # for uid in user_ids:
        #     room_group_name = f'chat_{min(user_id, uid)}_{max(user_id, uid)}'
        #     payload = {
        #         'type': 'send_status',
        #         'user_id': user_id,
        #         'is_online': is_online,
        #     }
        #     async_to_sync(channel_layer.group_send)(room_group_name, payload)

        active_conversation_record=ActiveConversation.objects.filter(chat_with_id=user_id)#this will fetch records of users wwho have opened one to one chat wwith this user.
        #so that wew can easily broadcast the status of this user to the users who have opened chat with this user in real time.
        for record in active_conversation_record:
            room_group_name = f'chat_{min(user_id, record.chat_opened_by.id)}_{max(user_id, record.chat_opened_by.id)}'
            payload = {
                'type': 'send_status',
                'user_id': user_id,
                'is_online': is_online,
            }
            async_to_sync(channel_layer.group_send)(room_group_name, payload)
            
    except Exception as e:
        print(f"Error in broadcast_user_status: {e}")