import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from chats_app.models import *
from auth_app.models import User
from channels.db import database_sync_to_async
from asgiref.sync import  sync_to_async
from django.db.models import Q
import traceback
from django.contrib.contenttypes.models import ContentType
from .redis_utils import *
from django.db.models.signals import post_save
from datetime import timedelta

@database_sync_to_async
def create_notification(self, sender_user_id, notification_type, content_type_id, object_id,is_personal_chat,notif_message=None):
    try:
        should_create_notification = False
        
        if notification_type in [
            'group_message',
            'group_member_joined',
            'group_member_left', 
            'group_member_removed',
            'new_group_admin',
            'replied_on_group_message',
            'group_message_deleted'
        ]:
            group_members = GroupMemberships.objects.filter(
                group_id=self.group_id
            ).exclude(user_id=sender_user_id)
            active_user_ids = get_active_users_in_group(self.room_group_name)
            inactive_group_members = [member for member in group_members if member.user.id not in active_user_ids]
            
            if inactive_group_members:
                should_create_notification = True
                
        elif is_personal_chat:
            receiver_user_id = self.scope['url_route']['kwargs']['receiver_id']
            is_user_active = is_user_active_in_personal_chat(user_id=receiver_user_id,room_name=self.room_group_name)
            if not is_user_active:
                should_create_notification = True

        if should_create_notification:
            notification = Notification.objects.create(
                sender_user_id=sender_user_id,
                notification_type=notification_type,
                content_type_id=content_type_id,
                object_id=object_id,
                notif_message=notif_message,
                content_object=ContentType.objects.get_for_id(content_type_id).get_object_for_this_type(id=object_id) 
            )

            if notification_type in [
                'group_message',
                'group_member_joined',
                'group_member_left', 
                'group_member_removed',
                'new_group_admin',
                'replied_on_group_message',
                'group_message_deleted'
            ]:
                read_statuses = [
                    NotificationReadStatus(
                        notification=notification,
                        user=member.user,
                        is_read=False
                    ) for member in inactive_group_members
                ]
                created_instances = NotificationReadStatus.objects.bulk_create(read_statuses)
                for instance in created_instances:
                    post_save.send(sender=NotificationReadStatus, instance=instance, created=True)
            else:
                NotificationReadStatus.objects.create(
                    notification=notification,
                    user_id=receiver_user_id,
                    is_read=False
                )
            
            print(f'NOTIFICATION OF ID : {notification.id} CREATED!!!')
            return True, notification
        
        return True, None

    except Exception as ex:
        print(traceback.format_exc())
        return False, None

@database_sync_to_async
def get_chat_summary(self, user_id, chat_type,chat_group_id=None,other_user=None):
    try:
        summary = UserChatSummary.objects.filter(
            user_id=user_id,
            chat_type=chat_type,
            chat_group_id = chat_group_id,
            other_user=other_user
        ).first()
        return True, summary
    except Exception as ex:
        print(traceback.format_exc())
        return False, None

@database_sync_to_async 
def create_chat_summary(self, user_id, chat_type, content_type_id, object_id, 
                       last_message_sender_id, last_message_time, unread_count=0,chat_group_id=None,other_user=None):
    try:
        summary = UserChatSummary.objects.create(
            user_id=user_id,
            chat_type=chat_type,
            content_type_id=content_type_id,
            object_id=object_id,
            last_message_sender_id=last_message_sender_id,
            last_message_time=last_message_time,
            unread_count=unread_count,
            last_message=ContentType.objects.get(id=content_type_id).get_object_for_this_type(id=object_id),
            chat_group_id = chat_group_id,
            other_user_id=other_user
        )
        return True, summary
    except Exception as ex:
        print(traceback.format_exc())
        return False, None

@database_sync_to_async
def update_chat_summary(self, summary, last_message_sender_id, last_message_time, unread_count=0, last_message=None):
    try:
        summary.last_message_sender_id = last_message_sender_id
        summary.last_message_time = last_message_time
        summary.unread_count = unread_count
        if last_message:
            summary.content_type = ContentType.objects.get_for_model(last_message.__class__)
            summary.object_id = last_message.id
        summary.save()
        return True, summary
    except Exception as ex:
        print(traceback.format_exc())
        return False, None

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
            await self.update_chat_summary_record(self.sender_id)
            mark_user_active_in_personal_chat(user_id=self.sender_id, room_name=self.room_group_name) 
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def update_chat_summary_record(self, user_id):
        try:
            # Get chat summary for this user and set unread count to 0
            chat_summary = UserChatSummary.objects.filter(
                user_id=user_id,
                chat_type='single',
                other_user_id=self.receiver_id
            ).first()
            
            if chat_summary:
                chat_summary.unread_count = 0
                chat_summary.save()
                return True
            return False
        except Exception as ex:
            print(traceback.format_exc())
            return False
        
    @database_sync_to_async
    def mark_notification_read(self,message_ids):
        try:
            group_message_content_type = ContentType.objects.get_for_model(ChatModel)
            unread_notifications = NotificationReadStatus.objects.filter(
                is_read=False,
                notification__notification_type__in=[
                    Notification.SINGLE_CHAT_MESSAGE, 
                    Notification.MESSAGE_DELETED,
                    Notification.REPLIED_ON_MESSAGE
                ],
                notification__object_id__in=message_ids,
                notification__content_type=group_message_content_type  # 
            )
            if unread_notifications:
                unread_notifications.update(is_read=True)
            return True
        except Exception as ex:
            return False
        
    async def disconnect(self, close_code):
        try:
            print('inside dis connect')
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.delete_active_conversation_record(self.sender_id,self.receiver_id)
            remove_user_from_personal_chat(user_id=self.sender_id, room_name=self.room_group_name) 
        except Exception as ex:            
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def is_first_chat_message(self, sender_id, receiver_id, chat_message):
        try:
            exists = ChatModel.objects.filter(
                (Q(sender_id=sender_id) & Q(receiver_id=receiver_id)) |
                (Q(sender_id=receiver_id) & Q(receiver_id=sender_id))
            ).exclude(id=chat_message.id).exists()
            return not exists
        except Exception as ex:
            print(traceback.format_exc())
            return False

    async def receive(self, text_data):
        try:
            print('inside receive')
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            reply_to_message_id= text_data_json.get('replyToMessageId')
            message_id = text_data_json.get('message_id')
            is_deleted = bool(text_data_json.get('msg_is_deleted',False)) #by default keep as false.
            sent_time = timezone.now()

            if message:
                reply_to_message = await self.get_message_record_by_id(reply_to_message_id) if reply_to_message_id else None
                chat_message = await self.create_chat_message(self.sender_id, self.receiver_id, message, sent_time, reply_to_message)
                # Check if this is first message between these users
                is_first_message = await self.is_first_chat_message(self.sender_id, self.receiver_id,chat_message)
                notif_record = await create_notification(
                    self,
                    sender_user_id=self.sender_id,
                    notification_type='reply_on_message' if reply_to_message_id else 'single_chat_message',
                    content_type_id=(await database_sync_to_async(ContentType.objects.get_for_model)(ChatModel)).id,
                    object_id=chat_message.id,
                    notif_message=f"New message from {self.scope['user'].username}",
                    is_personal_chat=True
                )
                
                content_type = await sync_to_async(ContentType.objects.get_for_model)(ChatModel)
                
                if is_first_message:
                    # Create summary for sender
                    await create_chat_summary(self, user_id=self.sender_id, chat_type='single', content_type_id=content_type.id,
                        object_id=chat_message.id, last_message_sender_id=self.sender_id, last_message_time=sent_time,
                        unread_count=0, other_user=self.receiver_id)

                    # Create summary for receiver
                    await create_chat_summary(self, user_id=self.receiver_id, chat_type='single', content_type_id=content_type.id,
                        object_id=chat_message.id, last_message_sender_id=self.sender_id, last_message_time=sent_time,
                        unread_count=1, other_user=self.sender_id)
                else:
                    # Update only receiver's summary
                    success, summary = await get_chat_summary(self, user_id=self.receiver_id, chat_type='single', other_user=self.sender_id)
                    if success and summary:
                        summary.unread_count += 1
                        await update_chat_summary(self, summary=summary, last_message_sender_id=self.sender_id, 
                            last_message_time=sent_time, unread_count=summary.unread_count,
                            last_message=chat_message)

                payload = {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.sender_id,
                    'receiver_id': self.receiver_id,
                    'sent_time': sent_time.isoformat(),
                    'is_read': chat_message.is_read,
                    'channel_name': self.channel_name,
                    'id':chat_message.id,
                    'sender_name':chat_message.sender.full_name or chat_message.sender_.username
                }

                if reply_to_message_id:
                    payload['reply_to_message_id'] = reply_to_message.id
                    payload['reply_to_message_val']=reply_to_message.message

                await self.channel_layer.group_send(self.room_group_name, payload)

            elif message_id and not is_deleted:
                await self.mark_message_as_read(message_id, sent_time)
                await self.mark_notification_read(message_id)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_read',
                        'message_id': message_id,
                        'read_time': sent_time.isoformat(),
                    }
                )
            elif is_deleted:
                curr_time = timezone.now()
                await self.delete_message_notification(message_id)
                await self.send_delete_notification_(message_id)

        except Exception as ex:
            
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
            sender_name = event.get("sender_name")

            await self.send(text_data=json.dumps({
                'event_name':"chat_message",
                'message': message,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'sent_time': sent_time,
                'is_read': is_read,
                'reply_to_message_id':reply_to_message_id,
                'reply_to_message_val':reply_to_message_val,
                'id':message_id,
                'sender_name':sender_name
            }))

        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    async def broadcast_deleted_message(self,event):
        try:
            deleted_message_id = event.get("message",{}).get("deleted_message_id")
            await self.send(text_data=json.dumps({
                'event_name': 'message_deleted',
                "deleted_message_id": deleted_message_id
            }))
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    async def broadcast_messages_read(self,sender_id,receiver_id):
        try:
            message_ids=await self.mark_messages_from_receiver_as_read(sender_id,receiver_id)
            await self.mark_notification_read(message_ids)
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
            
            print(traceback.format_exc())
            return False
        
    @database_sync_to_async
    def create_active_conversation_record(self,sender_id,receiver_id):
        try:
            active_conversation_record=ActiveConversation.objects.get_or_create(chat_opened_by_id=sender_id,chat_with_id=receiver_id)
            return True,"Success"
        except Exception as ex:
            
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
            self.user_id = self.scope.get('user').id
            self.room_group_name = f'group_chat_{self.group_id}'
            self.channel_name = self.channel_name
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            await self.update_chat_summary_record(self.user_id,self.group_id)
            mark_user_active_in_group(self.user_id, self.room_group_name) 
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def update_chat_summary_record(self, user_id,group_id):
        try:
            # Get chat summary for this user and set unread count to 0
            chat_summary = UserChatSummary.objects.filter(
                user_id=user_id,
                chat_type='group',
                chat_group=group_id
            ).first()            
            if chat_summary:
                chat_summary.unread_count = 0
                chat_summary.save()
                return True
            return False
        except Exception as ex:
            print(traceback.format_exc())
            return False
        
    async def disconnect(self, close_code):
        try:
            print('inside dis connect')
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            remove_user_from_group(user_id=self.user_id,group_channel_name=self.room_group_name)
        except Exception as ex:
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
            deleted_message_id = text_data_json.get("deleted_message_id")#only present when user deleted a message
            if type_of_event:
                if type_of_event=='markMessageRead':
                    await self.mark_message_as_read(id_of_msg_read_by_user,current_time)
                    await self.mark_notification_read(id_of_msg_read_by_user)
                    await self.broadcast_message_read_in_group(id_of_msg_read_by_user,current_time,sender_user,sender_name)

            if message and not type_of_event:#it means user sent a new message and we need to broadcast it into the group
                replied_to_msg = await self.get_message_of_replied_to_message(self.group_id,reply_to_message_id)
                reply_to_message_val = replied_to_msg.message if replied_to_msg else None
                msg_record=await self.create_message_record(self.group_id,sender_user,current_time,reply_to_message_id,message)
                msg_id = msg_record.id
                if msg_id:
                    content_type = await sync_to_async(ContentType.objects.get_for_model)(GroupMessages)
                    group_members = await self.get_group_members(self.group_id)

                    notif_record = await create_notification(
                        self,
                        sender_user_id=sender_user,
                        notification_type='reply_on_message' if reply_to_message_id else 'group_message',
                        content_type_id=(await sync_to_async(ContentType.objects.get_for_model)(GroupMessages)).id,
                        object_id=msg_id,
                        notif_message=f"New message from {self.scope['user'].username}",
                         is_personal_chat=False
                    )
                    
                    # Process group members with async for loop
                    async for member in group_members:
                        success, summary = await get_chat_summary(self, member.user.id, 'group', chat_group_id=self.group_id)
                        if success and summary:
                            # Update existing summary
                            unread_count = 1 if member.user.id != sender_user else 0
                            await update_chat_summary(self, summary, sender_user, current_time,
                                                    unread_count=unread_count, last_message=msg_record)
                        else:
                            # Create new summary for member
                            unread_count = 1 if member.user.id != sender_user else 0
                            await create_chat_summary(self, member.user.id, 'group', content_type.id, msg_id,
                                                   sender_user, current_time, unread_count=unread_count,
                                                   chat_group_id=self.group_id)
                    await self.create_message_deliveries_for_group(msg_id,sender_user)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type':'broadcast_sender_msg_in_group',
                            'message':message,
                            'message_id':msg_id,
                            'reply_to_message_id':reply_to_message_id,
                            'sender_id':sender_user,
                            'sender_name':sender_name,
                            'reply_to_message_val':reply_to_message_val,
                        }
                    )
        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def mark_message_as_read(self,message_id,read_time):#message_id is a list of message ids
        try:
            message_read=GroupMessageRead.objects.filter(group_message__id__in=message_id,user=self.scope['user'])
            message_read.update(read_at=read_time)
            return True
        except Exception as ex:
            print(traceback.format_exc())
            return False
        
    @database_sync_to_async
    def mark_notification_read(self,message_ids):
        try:
            group_message_content_type = ContentType.objects.get_for_model(GroupMessages)
            unread_notifications = NotificationReadStatus.objects.filter(
                is_read=False,
                notification__notification_type__in=[
                    Notification.GROUP_MESSAGE, 
                    Notification.GROUP_MEMBERS_ADD,
                    Notification.GROUP_MEMBER_LEFT, 
                    Notification.GROUP_MEMBER_REMOVED,
                    Notification.NEW_GROUP_ADMIN, 
                    Notification.REPLIED_ON_GROUP_MESSAGE, 
                    Notification.GROUP_MESSAGE_DELETED
                ],
                notification__object_id__in=message_ids,
                notification__content_type=group_message_content_type  # 
            )
            if unread_notifications:
                unread_notifications.update(is_read=True)
            return True
        except Exception as ex:
            return False

    @database_sync_to_async
    def is_first_group_message(self, group_id,message_id):
        try:
            return not GroupMessages.objects.filter(group_id=group_id).exclude(id=message_id).exists()
        except Exception as ex:
            print(traceback.format_exc())
            return False

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
            
            print(traceback.format_exc())
            await self.close()

    async def broadcast_deleted_message(self,event):
        try:
            deleted_message_id = event.get("message",{}).get("deleted_message_id")
            await self.send(text_data=json.dumps({
                'event_name': 'message_deleted',
                "deleted_message_id": deleted_message_id
            }))
        except Exception as ex:
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
            
            print(traceback.format_exc())
            await self.close()

    async def broadcast_deleted_group_message(self,event):
        try:
            deleted_message_id = event.get("deleted_message_id")
            await self.send(text_data=json.dumps({
                'event_name':'message_deleted',
                "deleted_message_id":deleted_message_id
            }))
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    async def broadcast_sender_msg_in_group(self,event):
        try:
            message=event['message'] if 'message' in event else None
            message_id=event['message_id'] if 'message_id' in event else None
            reply_to_message_id=event['reply_to_message_id'] if 'reply_to_message_id' in event else None
            sender_id=event['sender_id'] if 'sender_id' in event else None
            reply_to_message_val = event['reply_to_message_val'] if 'reply_to_message_val' in event else None
            sender_name = event['sender_name'] if 'sender_name' in event else None
            await self.send(text_data=json.dumps({
                'message':message,
                'message_id':message_id,
                'reply_to_message_id':reply_to_message_id,
                'event_name':'chat_message',
                'sender_id':sender_id,
                'reply_to_message_val':reply_to_message_val,
                'sender_name':sender_name

            }))
        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    async def send_participant_removal_msg_for_group(self,event):
        try:
            print('inside send_participant_removal_msg_for_group',event)
            deleted_user_id=event.get("message",{}).get("deleted_user_id")
            deleted_user_name=event.get("message",{}).get("deleted_user_name") 
            deleted_by_user_id = event.get("message",{}).get('deleted_by_user_id')
            deleted_by_user_name= event.get("message",{}).get("deleted_by_user_name")
            message = event.get("message",{}).get('message')
            await self.send(text_data=json.dumps({
                'message':message,
                'deleted_by_user_name':deleted_by_user_name,
                'deleted_by_user_id':deleted_by_user_id,
                'event_name':'participant_removal',
                'deleted_user_id':deleted_user_id,
                'deleted_user_name':deleted_user_name
            }))
        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def create_message_deliveries_for_group(self, message_id,user_id):
        try:
            users = GroupMemberships.objects.filter(group__id=self.group_id).exclude(user=user_id)
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
    def get_message_of_replied_to_message(self,group_id,reply_to_msg_id):
        try:
            message = GroupMessages.objects.get(
                group_id=group_id,
                id=reply_to_msg_id
            )
            return message
        except Exception as ex:
            return None
        
    @database_sync_to_async
    def create_message_record(self,group_id,sender_user,message_sent_time,reply_to_message_id,message):
        message = GroupMessages.objects.create(
            group_id=group_id,
            sender_id=sender_user,
            message=message,
            sent_time=message_sent_time,
            parent_message_id=reply_to_message_id
        )
        return message
        
    @database_sync_to_async
    def get_group_members(self,group_id):
        group_members = GroupMemberships.objects.filter(group_id=group_id).select_related('user')
        return group_members
    
class UserStatus(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            print('inside connect')
            self.user_id = self.scope['url_route']['kwargs']['user_id']
            self.room_group_name = f'user_status_{self.user_id}'
            self.channel_name = self.channel_name
            
            # Add to user status group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Mark user as online
            await self.update_online_status(True)

            await self.accept()

            # Get all active conversations with this user
            active_chats = await self.get_active_conversations()

            # Broadcast online status to all users who have active chats with this user
            for chat in active_chats:
                other_user_group = f'user_status_{chat.chat_opened_by_id}'
                await self.channel_layer.group_send(
                    other_user_group,
                    {
                        'type': 'user_status',
                        'is_online': True,
                        'user_id': self.user_id
                    }
                )

        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        try:
            print('inside disconnect')
            
            await self.update_online_status(False)

            active_chats = await self.get_active_conversations()

            # Broadcast offline status to all users who have active chats with this user
            for chat in active_chats:
                other_user_group = f'user_status_{chat.chat_opened_by_id}'
                await self.channel_layer.group_send(
                    other_user_group,
                    {
                        'type': 'user_status',
                        'is_online': False,
                        'user_id': self.user_id
                    }
                )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            
        except Exception as ex:
            
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def update_online_status(self, is_online):
        User.objects.filter(id=self.user_id).update(is_online=is_online)

    @database_sync_to_async
    def get_active_conversations(self):
        # Get all active conversations where this user is involved
        return list(ActiveConversation.objects.filter(chat_with_id=self.user_id))

    async def user_status(self, event):
        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'is_online': event['is_online'],
            'user_id': event['user_id']
        }))

class Notifications(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user_id = self.scope['user'].id
            self.room_group_name = f'notifications_{self.user_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    async def notification_message(self, event):
        try:
            print('inside notification_message')
            url = ''
            notification,url = await self.get_notification(event.get('notification_id'))
            
            if notification:
                content_obj = await database_sync_to_async(lambda: notification.content_object)()

            print(f'url: {url}')
            last_message_body = content_obj.message if content_obj else None

            notification_data = {
                'type': event['type'],
                'message': event['message'],
                'data': event.get('data', {}),
                'notification_id': event.get('notification_id'),
                'created_at': event.get('created_at'), 
                'notification_type': event.get('notification_type'),
                'sender': event.get('sender'),
                'last_message_body':last_message_body,
                'url': url
            }
            await self.send(text_data=json.dumps(notification_data))
        except Exception as ex:
            print(traceback.format_exc())
            await self.close()

    @database_sync_to_async
    def get_notification(self, notification_id):
        try:
            notif_record = Notification.objects.select_related('content_type', 'sender_user').get(id=notification_id)
            if isinstance(notif_record.content_object,ChatModel):
                url = f'/chats_page/{notif_record.content_object.sender.id}/'
            elif isinstance(notif_record.content_object,GroupMessages):
                url = f'/group_chat/{notif_record.content_object.group.id}/'
            return notif_record,url
        except Notification.DoesNotExist:
            return None
