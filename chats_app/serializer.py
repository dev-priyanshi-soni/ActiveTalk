from .models import *
from rest_framework import serializers


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
                'receiver': obj.parent_message.receiver.id
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

