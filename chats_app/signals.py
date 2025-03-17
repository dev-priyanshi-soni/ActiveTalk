from django.contrib.auth.signals import user_logged_in,user_logged_out
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save,post_delete
from .models import NotificationReadStatus, Notification
from django.contrib.contenttypes.models import ContentType


# @receiver(user_logged_in)
# def user_logged_in_handler(sender, request, user, **kwargs):
#     user.is_online=True
#     user.save()
#     broadcast_user_status(user.id, True)

# @receiver(user_logged_out)
# def user_logged_out_handler(sender, request, user, **kwargs):
#     user.is_online=False
#     user.save()
#     broadcast_user_status(user.id, False)

# def broadcast_user_status(user_id, is_online):
#     try:
#         channel_layer = get_channel_layer()

#         # chat_pairs = ChatModel.objects.filter(
#         #     Q(sender_id=user_id) | Q(receiver_id=user_id),
#         #     sent_time__gte=timezone.now() - timezone.timedelta(hours=12)
#         # ).values_list('sender_id', 'receiver_id')
#         # user_ids = {id for pair in chat_pairs for id in pair} - {user_id}

#         # for uid in user_ids:
#         #     room_group_name = f'chat_{min(user_id, uid)}_{max(user_id, uid)}'
#         #     payload = {
#         #         'type': 'send_status',
#         #         'user_id': user_id,
#         #         'is_online': is_online,
#         #     }
#         #     async_to_sync(channel_layer.group_send)(room_group_name, payload)

#         active_conversation_record=ActiveConversation.objects.filter(chat_with_id=user_id)#this will fetch records of users wwho have opened one to one chat wwith this user.
#         #so that wew can easily broadcast the status of this user to the users who have opened chat with this user in real time.
#         for record in active_conversation_record:
#             room_group_name = f'chat_{min(user_id, record.chat_opened_by.id)}_{max(user_id, record.chat_opened_by.id)}'
#             payload = {
#                 'type': 'send_status',
#                 'user_id': user_id,
#                 'is_online': is_online,
#             }
#             async_to_sync(channel_layer.group_send)(room_group_name, payload)
            
#     except Exception as e:
#         print(f"Error in broadcast_user_status: {e}")

@receiver(post_save, sender=NotificationReadStatus)
def send_notification_status(sender, instance, created, **kwargs):
    if created:
        try:
            channel_layer = get_channel_layer()
            notification = instance.notification
            
            notification_data = {
                'type': 'notification_message',
                'message': notification.notif_message,
                'notification_id': notification.id,
                'created_at': notification.timestamp.isoformat(),
                'notification_type': notification.notification_type,
                'sender': notification.sender_user_id,
                'data': {},
                'read_status_id': instance.id,
                'is_read': instance.is_read
            }

            room_group_name = f'notifications_{instance.user.id}'
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                notification_data
            )

        except Exception as e:
            print(f"Error sending notification status: {e}")



@receiver(post_delete, sender=Notification)
def delete_generic_related_objects(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    related_objects = Notification.objects.filter(
        content_type=content_type, object_id=instance.id
    )
    related_objects.delete()
