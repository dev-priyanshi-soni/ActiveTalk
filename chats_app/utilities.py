from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Group,GroupMemberships,GroupMessages,ChatModel
import traceback

def send_event_for_group_member_removal(group_id:int,deleted_group_member,deleted_by_user):
    channel_layer = get_channel_layer()
    message = f'{deleted_by_user.username} removed {deleted_group_member.user.username}'
    async_to_sync(channel_layer.group_send)(
        f"group_chat_{group_id}",
        {
            "type": "send_participant_removal_msg_for_group",  
            "message": {
                'deleted_user_id':deleted_group_member.user.id,
                'deleted_user_name':deleted_group_member.user.username,
                'deleted_by_user_id':deleted_by_user.id,
                'deleted_by_user_name':deleted_by_user.username,
                'message':message
            }
        }
    )


def check_user_group_membership(group_id,user_id):
    try:
        group_data = Group.objects.filter(id=group_id)
        if not group_data.exists():
            return False,"Group not exists"
        group_member_data = GroupMemberships.objects.filter(group__id=group_id,user__id=user_id)
        if not group_member_data:
            return False,"You are not a participant"
        return True,"Success"
    except Exception as ex:
        
        print(traceback.format_exc())
        return False,"Some Error occurred"

def create_event_for_deleted_group_message(group_msg_rec:GroupMessages):
    try:
        '''
        This will hide the message from other users and make it as This message was deleted in real-time.
        '''
        group_id = group_msg_rec.group.id
        channel_layer = get_channel_layer()
        message = f'This message was deleted'
        async_to_sync(channel_layer.group_send)(
            f"group_chat_{group_id}",
            {
                "type": "broadcast_deleted_message",  
                "message": {
                    'deleted_message_id':group_msg_rec.id,
                }
            }
        )
        return True,"Success"
    except Exception as ex:
        return False,str(ex)
    
def create_event_for_deleted_personal_chat_message(chat_message_rec:ChatModel):
    try:
        room_group_name = f'chat_{min(chat_message_rec.sender_id,chat_message_rec.receiver_id)}_{max(chat_message_rec.sender_id,chat_message_rec.receiver_id)}'
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"{room_group_name}",
            {
                "type":"broadcast_deleted_message",
                "message":{
                    "deleted_message_id":chat_message_rec.id,
                }
            }
        )

        return True,"Success"
    except Exception as ex:
        return False,str(ex)
