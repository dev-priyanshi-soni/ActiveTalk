from .models import *
from rest_framework import serializers
from auth_app.serializers import UserSerializer

class ChatModelSerializer(serializers.ModelSerializer):
    parent_message = serializers.SerializerMethodField()
    class Meta:
        model = ChatModel
        fields = '__all__'

    def get_parent_message(self, obj):
        if obj.parent_message:
            return {
                'id': obj.parent_message.id,
                'message': obj.parent_message.message,
                'sender': obj.parent_message.sender.id,
                'sender_full_name': obj.parent_message.sender.full_name,
                'receiver': obj.parent_message.receiver.id
            }
        return None
        

class GroupChatsModelSerializer(serializers.ModelSerializer):
    parent_message = serializers.SerializerMethodField()
    sender_name=serializers.SerializerMethodField()
    is_read_by_all=serializers.SerializerMethodField()
    class Meta:
        model = GroupMessages
        fields = '__all__'

    def get_parent_message(self, obj):
        if obj.parent_message:
            return {
                'id': obj.parent_message.id,
                'message': obj.parent_message.message,
                'sender': obj.parent_message.sender.id,
                'sender_full_name': obj.parent_message.sender.full_name,
            }
        return None
    
    def get_sender_name(self,obj):
        if obj.sender:
            return obj.sender.full_name
        
    def get_is_read_by_all(self,obj):
        is_read_by_all = GroupMemberships.objects.filter(group=obj.group.id,joined_at__lt=obj.sent_time).exclude(user=self.context['user'].id).count() == GroupMessageRead.objects.filter(group_message=obj.id, read_at__isnull=False).values('user').distinct().count()
        return is_read_by_all
        
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class GroupMembershipsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMemberships
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['member_id']=instance.user.id if instance.user else None
        representation['member_full_name']=instance.user.full_name if instance.user else None
        representation['read_at']=instance.read_at if instance.read_at else None
        representation['delivered_at']=instance.delivered_at if instance.delivered_at else None
        return representation
    

class GroupMembershipsDataSerializer(serializers.ModelSerializer):
    group_member_name=serializers.SerializerMethodField()
    class Meta:
        model = GroupMemberships
        fields = '__all__'

    def get_group_member_name(self,obj):
        return obj.user.full_name if obj.user else None


class UserChatSummarySerializer(serializers.Serializer):
    chat_type = serializers.CharField()
    last_message_time = serializers.DateTimeField()
    unread_count = serializers.IntegerField()
    last_message_sender = UserSerializer()
    chat_with = serializers.SerializerMethodField()
    group = GroupSerializer(required=False)
    last_message_id = serializers.SerializerMethodField()
    last_message_sent_body = serializers.SerializerMethodField() 
    last_message_sent_by_id = serializers.SerializerMethodField()
    last_message_sent_by_full_name = serializers.SerializerMethodField()
    url_of_chat_page = serializers.SerializerMethodField()

    def get_last_message_id(self, obj):
        return obj.object_id if obj.object_id else None
    
    def get_last_message_sent_body(self, obj):
        try:
            if obj.content_type and obj.object_id:
                message = obj.content_type.get_object_for_this_type(id=obj.object_id)
                return getattr(message, 'message', None)
        except Exception as e:
            return None 
        return None

    def get_last_message_sent_by_id(self, obj):
        if obj.last_message_sender:
            return obj.last_message_sender.id
        return None

    def get_last_message_sent_by_full_name(self, obj):
        if obj.last_message_sender:
            return obj.last_message_sender.full_name
        return None
    
    def get_url_of_chat_page(self,obj):
        if obj.chat_type == 'single':
            chat_with = obj.other_user
            if chat_with:
                return f'/chats_page/{chat_with.id}/'
        else:
            # For group chats
            group = obj.chat_group
            if group:
                return f'/group_chat/{group.id}/'
        return None
    
    def get_chat_with(self,obj):
        if obj.chat_type == 'single':
            return obj.other_user.full_name or obj.other_user.username if obj.other_user else None
        else:
            # For group chats
            return obj.chat_group.name if obj.chat_group else None



class NotificationReadStatusSerializer(serializers.ModelSerializer):
    notification_message = serializers.CharField(source='notification.notif_message')
    notification_type = serializers.CharField(source='notification.notification_type')
    created_at = serializers.DateTimeField(source='notification.timestamp')
    sender_id = serializers.IntegerField(source='notification.sender_user_id')

    class Meta:
        model = NotificationReadStatus
        fields = ['id', 'notification_message', 'notification_type', 'created_at', 'sender_id', 'is_read']
