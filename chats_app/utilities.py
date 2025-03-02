from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Group,GroupMemberships

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
        import traceback
        print(traceback.format_exc())
        return False,"Some Error occurred"