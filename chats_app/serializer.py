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
        