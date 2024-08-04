import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from chats_app.models import ChatModel
from auth_app.models import User
from channels.db import database_sync_to_async
from asgiref.sync import  sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            print('inside connect')
            self.sender_id = self.scope['url_route']['kwargs']['sender_id']
            self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
            print('rec',self.receiver_id,'send',self.sender_id)
            self.room_group_name = f'chat_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'
            self.channel_name = self.channel_name
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.broadcast_user_status(self.sender_id,True,self.receiver_id)
            await self.broadcast_messages_read(self.sender_id,self.receiver_id)
            
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
            await self.broadcast_user_status(self.sender_id,False,None)
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
                    'id':chat_message.id
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
            message_id=event['id'] if 'id' in event else None

            await self.send(text_data=json.dumps({
                'event_name':"chat_message",
                'message': message,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'sent_time': sent_time,
                'is_read': is_read,
                'reply_to_message_id':reply_to_message_id,
                'reply_to_message_val':reply_to_message_val,
                'id':message_id
            }))

        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()


    async def broadcast_messages_read(self,sender_id,receiver_id):
        try:
            message_ids=await self.mark_messages_from_receiver_as_read(sender_id,receiver_id)
            print('message_ids',message_ids)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type':'mark_msg_read',
                    'receiver_id':receiver_id,
                    'sender_id':sender_id,
                    'message_ids':message_ids
                }
            )

        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def mark_msg_read(self,event):
        try:
            receiver_id=event['receiver_id'] if 'receiver_id' in event else None
            sender_id=event['sender_id'] if 'sender_id' in event else None
            message_ids=event['message_ids'] if 'message_ids' in event else None
            if receiver_id != sender_id:
                await self.send(text_data=json.dumps({
                    'event_name':"msg_read",
                    'receiver_id':receiver_id,
                    'sender_id':sender_id,
                    'message_ids':message_ids

                }))

        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()


    async def broadcast_user_status(self,user_id,is_online,reciever_id):
        try:
            receiver_status=None
            
            if not is_online:
                await self.set_user_offline(user_id)
                receiver_status=False
            else:
                await self.set_user_online(user_id)
                if reciever_id:
                    receiver_status=await self.get_reciever_status(reciever_id)
                
                    

            await self.channel_layer.group_send(
                self.room_group_name,
                {   
                    'type':'send_status',
                    'user_id':user_id,
                    'is_online':is_online,
                    'receiver_status':receiver_status
                }
            )
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
         
    async def send_status(self,event):
        try:
            user_id=event['user_id'] if 'user_id' in event else None
            is_online=event['is_online'] if 'is_online' in event else None
            receiver_status=event['receiver_status'] if 'receiver_status' in event else None
            await self.send(text_data=json.dumps({
                'event_name':"status",
                'user_id':user_id,
                'is_online':is_online,
                'receiver_status':receiver_status
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
                'event_name':"message_read",
                'message_id': message_id,
                'read_time': read_time,
                'is_read': True,
            }))
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    def get_user_online_status(self,user_id):
        # user_rec=User.objects.filter(id=user_id)
        # if user_rec.exists():
        #     user_rec=user_rec.last()
        #     return user_rec.is_active
        # return False
        try:
            user_rec = User.objects.get(id=user_id)  # Use get() for direct access
            return user_rec.is_active
        except User.DoesNotExist:
            return False

    async def get_reciever_status(self,user_id):
        try:
            user_online_status=await sync_to_async(self.get_user_online_status)(user_id)
            return user_online_status

        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            return False

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
        return None

    @database_sync_to_async
    def set_user_online(self, user_id):
        user_profile = User.objects.get(id=user_id)
        user_profile.is_online = True
        user_profile.last_seen = timezone.now()
        user_profile.save()
        return None

    @database_sync_to_async
    def set_user_offline(self, user_id):
        user_profile = User.objects.get(id=user_id)
        user_profile.is_online = False
        user_profile.last_seen = timezone.now()
        user_profile.save()
        return None
    
    @database_sync_to_async
    def mark_messages_from_receiver_as_read(self,sender_id,receiver_id):
        messages = ChatModel.objects.filter(sender=receiver_id,receiver=sender_id,is_read=False)
        message_ids = list(messages.values_list('id', flat=True))  
        messages.update(is_read=True,read_time=timezone.now())
        return message_ids