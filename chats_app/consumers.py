import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from chats_app.models import *
from auth_app.models import User
from channels.db import database_sync_to_async
from asgiref.sync import  sync_to_async
from django.db.models import Q

# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# import redis
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
# channel_layer = get_channel_layer()

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
            
            await self.broadcast_messages_read(self.sender_id,self.receiver_id)
            await self.accept()
            await self.send_receiver_user_status(self.receiver_id)
            await self.create_active_conversation_record(self.sender_id,self.receiver_id)
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
            await self.delete_active_conversation_record(self.sender_id,self.receiver_id)
            # Mark sender as offline
            # await self.broadcast_user_status(self.sender_id,False,None)
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
         
    async def send_status(self,event):
        try:
            active_user_id=event['user_id'] if 'user_id' in event else None
            is_online=event['is_online'] if 'is_online' in event else None

            await self.send(text_data=json.dumps({
                'event_name':"status",
                'user_id':active_user_id,
                'is_online':is_online
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
        try:
            user_rec = User.objects.get(id=user_id)  # Use get() for direct access
            return user_rec.is_online
        except User.DoesNotExist:
            return False

    async def send_receiver_user_status(self,user_id):
        try:
            user_online_status=await sync_to_async(self.get_user_online_status)(user_id)
            await self.send(text_data=json.dumps({
                'event_name':'status',
                'user_id':user_id,
                'is_online':user_online_status

            }))

        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            return False
        
    @database_sync_to_async
    def create_active_conversation_record(self,sender_id,receiver_id):
        try:
            active_conversation_record=ActiveConversation.objects.get_or_create(chat_opened_by_id=sender_id,chat_with_id=receiver_id)
            return True,"Success"
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return False,str(ex)
        
    @database_sync_to_async
    def delete_active_conversation_record(self,sender_id,receiver_id):
        try:
            active_conversation_record=ActiveConversation.objects.filter(chat_opened_by_id=sender_id,chat_with_id=receiver_id)
            if active_conversation_record.exists():
                active_conversation_record.delete()
            return True,"Success"
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return False,str(ex)
            
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
    def mark_messages_from_receiver_as_read(self,sender_id,receiver_id):
        messages = ChatModel.objects.filter(sender=receiver_id,receiver=sender_id,is_read=False)
        message_ids = list(messages.values_list('id', flat=True))  
        messages.update(is_read=True,read_time=timezone.now())
        return message_ids
    

class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            print('inside connect')
            self.group_id = self.scope['url_route']['kwargs']['group_id']
            self.room_group_name = f'group_chat_{self.group_id}'
            self.channel_name = self.channel_name
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            # key = f"{self.channel_name}__{self.scope['user'].id}"
            # redis_client.set(key,self.scope['user'].id)
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
            # key = f"{self.channel_name}__{self.scope['user'].id}"
            # redis_client.delete(key)
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def receive(self, text_data):
        try:
            current_time=timezone.now()
            sender_user=self.scope['user'].id
            sender_name=self.scope['user'].full_name
            print('inside receive')
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            id_of_msg_read_by_user=text_data_json.get('messageIds')#its a list of message ids
            type_of_event=text_data_json.get('type_of_event')
            reply_to_message_id=text_data_json.get("reply_to_message_id")
            if type_of_event:
                if type_of_event=='markMessageRead':
                    await self.mark_message_as_read(id_of_msg_read_by_user,current_time)
                    await self.broadcast_message_read_in_group(id_of_msg_read_by_user,current_time,sender_user,sender_name)
            if message and not type_of_event:#it means user sent a new message and we need to broadcast it into the group
                msg_id=await self.create_message_record(self.group_id,sender_user,current_time,reply_to_message_id,message)
                if msg_id:
                    await self.create_message_deliveries_for_group(msg_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type':'broadcast_sender_msg_in_group',
                            'message':message,
                            'message_id':msg_id,
                            'reply_to_message_id':reply_to_message_id,
                            'sender_id':sender_user,
                            'sender_name':sender_name

                        }
                    )
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()
    
    @database_sync_to_async
    def mark_message_as_read(self,message_id,read_time):#message_id is a list of message ids
        try:
            message_read=GroupMessageRead.objects.filter(group_message__id__in=message_id,user=self.scope['user'])
            message_read.update(read_at=read_time)
        except Exception as ex:
            import traceback
            print(traceback.format_exc())

    async def broadcast_message_read_in_group(self,message_id,read_at,sender_user,sender_name):
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type':'broadcast_message_read_by_user_in_group',
                    'message_id':message_id,
                    'read_at':str(read_at),
                    'sender_id':sender_user,
                    'sender_name':sender_name
                }
            )
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def broadcast_message_read_by_user_in_group(self,event):
        try:
            message_id=event['message_id'] if 'message_id' in event else None
            read_at=event['read_at'] if 'read_at' in event else None
            sender_id=event['sender_id'] if 'sender_id' in event else None
            sender_name=event['sender_name'] if 'sender_name' in event else None
            await self.send(text_data=json.dumps({
                'message_id':str(message_id),
                'read_at':str(read_at),
                'sender_name':sender_name,
                'sender_id':sender_id,
                'event_name':'message_read_by_user_in_group'
            }))
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    async def broadcast_sender_msg_in_group(self,event):
        try:
            message=event['message'] if 'message' in event else None
            message_id=event['message_id'] if 'message_id' in event else None
            reply_to_message_id=event['reply_to_message_id'] if 'reply_to_message_id' in event else None
            sender_id=event['sender_id'] if 'sender_id' in event else None
            await self.send(text_data=json.dumps({
                'message':message,
                'message_id':message_id,
                'reply_to_message_id':reply_to_message_id,
                'event_name':'chat_message',
                'sender_id':sender_id

            }))
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def create_message_deliveries_for_group(self, message_id):
        try:
            users = GroupMemberships.objects.filter(group__id=self.group_id)
            now = timezone.now()
            deliveries = []
            for user in users:
                deliveries.append(
                    GroupMessageRead(
                        group_message_id=message_id,
                        user_id=user.user.id,
                        delivered_time=now if user.user.is_online else None,
                        read_at=None
                    )
                )
            # Bulk create all delivery records
            GroupMessageRead.objects.bulk_create(deliveries)
            return True
        except Exception as ex:
            return False
        
    @database_sync_to_async
    def create_message_record(self,group_id,sender_user,message_sent_time,reply_to_message_id,message):
        message = GroupMessages.objects.create(
            group_id=group_id,
            sender_id=sender_user,
            message=message,
            sent_time=message_sent_time,
            parent_message_id=reply_to_message_id
        )
        return message.id
        
    @database_sync_to_async
    def get_group_members(group_id):
        group_members = GroupMemberships.objects.filter(group_id=group_id).select_related('user')
        return group_members