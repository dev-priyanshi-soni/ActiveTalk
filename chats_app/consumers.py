import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from chats_app.models import ChatModel
from auth_app.models import User
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            print('inside connect')
            self.sender_id = self.scope['url_route']['kwargs']['sender_id']
            self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
            self.room_group_name = f'chat_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'
            self.channel_name = self.channel_name
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.set_user_online(self.sender_id)
            await self.mark_messages_from_receiver_as_read(self.sender_id,self.receiver_id)
            await self.accept()
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        try:
            print('inside dis connect')
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Mark sender as offline
            await self.set_user_offline(self.sender_id)
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def receive(self, text_data):
        try:
            print('inside receive')
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            reply_to_message_id= text_data_json.get('replyToMessageId')
            message_id = text_data_json.get('message_id')
            sent_time = timezone.now()

            if message:
                reply_to_message = await self.get_message_record_by_id(reply_to_message_id) if reply_to_message_id else None
                chat_message = await self.create_chat_message(self.sender_id, self.receiver_id, message, sent_time, reply_to_message)

                payload = {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.sender_id,
                    'receiver_id': self.receiver_id,
                    'sent_time': sent_time.isoformat(),
                    'is_read': chat_message.is_read,
                    'channel_name': self.channel_name,
                }

                if reply_to_message_id:
                    payload['reply_to_message_id'] = reply_to_message.id
                    payload['reply_to_message_val']=reply_to_message.message

                await self.channel_layer.group_send(self.room_group_name, payload)

            elif message_id:
                await self.mark_message_as_read(message_id, sent_time)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_read',
                        'message_id': message_id,
                        'read_time': sent_time.isoformat(),
                    }
                )
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def chat_message(self, event):
        try:
            message = event['message']
            sender_id = event['sender_id']
            receiver_id = event['receiver_id']
            sent_time = event['sent_time']
            is_read = event['is_read']
            reply_to_message_id=event['reply_to_message_id'] if 'reply_to_message_id' in event else None
            reply_to_message_val=event['reply_to_message_val'] if 'reply_to_message_val' in event else None

            await self.send(text_data=json.dumps({
                'message': message,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'sent_time': sent_time,
                'is_read': is_read,
                'reply_to_message_id':reply_to_message_id,
                'reply_to_message_val':reply_to_message_val
            }))
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def message_read(self, event):
        try:
            message_id = event['message_id']
            read_time = event['read_time']

            await self.send(text_data=json.dumps({
                'message_id': message_id,
                'read_time': read_time,
                'is_read': True,
            }))
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def get_message_record_by_id(self, message_id):
        chat_record=ChatModel.objects.filter(id=message_id)
        return chat_record.last() if chat_record.exists() else None

    @database_sync_to_async
    def create_chat_message(self, sender_id, receiver_id, message, sent_time,replying_to_message=None):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        chat_message = ChatModel.objects.create(sender=sender, receiver=receiver, message=message, sent_time=sent_time,parent_message=replying_to_message)
        return chat_message

    @database_sync_to_async
    def mark_message_as_read(self, message_id, read_time):
        chat_message = ChatModel.objects.get(id=message_id)
        chat_message.is_read = True
        chat_message.read_time = read_time
        chat_message.save()

    @database_sync_to_async
    def set_user_online(self, user_id):
        user_profile = User.objects.get(id=user_id)
        user_profile.is_online = True
        user_profile.last_seen = timezone.now()
        user_profile.save()

    @database_sync_to_async
    def set_user_offline(self, user_id):
        user_profile = User.objects.get(id=user_id)
        user_profile.is_online = False
        user_profile.last_seen = timezone.now()
        user_profile.save()

    @database_sync_to_async
    def mark_messages_from_receiver_as_read(self,sender_id,receiver_id):
        messages = ChatModel.objects.filter(sender=receiver_id,receiver=sender_id,is_read=False)
        messages.update(is_read=True,read_time=timezone.now())