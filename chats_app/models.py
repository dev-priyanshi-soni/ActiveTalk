from django.db import models
from auth_app.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ChatModel(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.SET_NULL, null=True)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.SET_NULL, null=True)
    message = models.CharField(max_length=300, null=True, blank=True)
    is_read = models.BooleanField(default=False)#this points the time if receiver read the message
    read_time = models.DateTimeField(null=True, blank=True)#this points the time when receiver read the message
    sent_time = models.DateTimeField(auto_now_add=True)#this points the time when sender sent the message
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    parent_message = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.SET_NULL) 
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True,blank=True)

class ActiveConversation(models.Model):
    #here records will be created when user opens a chat with another user so that we can
    # broadcast status of other user in real time to the user who has opened chat.
    chat_opened_by = models.ForeignKey(User, related_name='chat_opened_by', on_delete=models.SET_NULL, null=True)
    chat_with = models.ForeignKey(User, related_name='chat_with', on_delete=models.SET_NULL, null=True)

class Group(models.Model):   
    name=models.CharField(max_length=400,null=True,blank=True)
    users=models.ManyToManyField(User,through='GroupMemberships',related_name="group_users")
    created_at=models.DateTimeField(null=False,auto_now_add=True)
    created_by= models.ForeignKey(to=User,on_delete=models.SET_NULL,null=True)

class GroupMemberships(models.Model):  
    user=models.ForeignKey(to=User,on_delete=models.SET_NULL,null=True)
    is_admin=models.BooleanField(default=False)
    group=models.ForeignKey(to=Group,on_delete=models.SET_NULL,null=True)
    joined_at=models.DateTimeField(auto_now_add=True)

class GroupMessages(models.Model): 
    group = models.ForeignKey(to=Group,related_name="group",on_delete=models.CASCADE)
    sender = models.ForeignKey(to=User,related_name='group_msg_sender_user' ,on_delete=models.SET_NULL,null=True)
    message = models.CharField(max_length=300,null=True,blank=True)
    sent_time = models.DateTimeField(null=False)
    file = models.FileField(upload_to='group_chat_files/', null=True, blank=True) 
    parent_message = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.SET_NULL)  
    is_deleted = models.BooleanField(default=False)#user can delete within a minute of sending. Other users view as deleted message 
    deleted_at = models.DateTimeField(blank=True,null=True) #refers to deleted time of the group message

class GroupMessageRead(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True,null=True)
    group_message = models.ForeignKey(GroupMessages, on_delete=models.CASCADE, db_index=True,null=True)
    read_at = models.DateTimeField(null=True,blank=True)
    delivered_time = models.DateTimeField(null=True, blank=True)


class Notification(models.Model):

    SINGLE_CHAT_MESSAGE = 'single_chat_message'
    GROUP_MESSAGE = 'group_message'
    GROUP_MEMBERS_ADD = 'group_member_joined'
    GROUP_MEMBER_LEFT = 'group_member_left'
    GROUP_MEMBER_REMOVED = 'group_member_removed'
    NEW_GROUP_ADMIN = 'new_group_admin'
    MESSAGE_DELETED = 'message_deleted'
    REPLIED_ON_MESSAGE = 'reply_on_message'
    REPLIED_ON_GROUP_MESSAGE = 'replied_on_group_message'
    GROUP_MESSAGE_DELETED = 'group_message_deleted'

    NOTIFICATION_TYPES = [
        (SINGLE_CHAT_MESSAGE, 'New message in single chat'), #for single chat
        (GROUP_MESSAGE, 'New message in group'),
        (GROUP_MEMBERS_ADD, 'New group member joined'),
        (GROUP_MEMBER_LEFT, 'Member left group'),
        (GROUP_MEMBER_REMOVED, 'Member removed from group'),
        (NEW_GROUP_ADMIN, 'New admin appointed'),
        (MESSAGE_DELETED, 'Message was deleted'), #for single chat
        (REPLIED_ON_MESSAGE,'Replied on message'), #for single chat
        (REPLIED_ON_GROUP_MESSAGE,'Replied on group message'),
        (GROUP_MESSAGE_DELETED, 'Group Message was deleted'),
    ]
 
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sender')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    notif_message = models.CharField(max_length=500,null=True,blank=True)

    class Meta:  
        ordering = ['-timestamp']

    def __str__(self): 
        return f'{self.user.username} - {self.get_notification_type_display()}'

class NotificationReadStatus(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='read_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_reads')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def mark_as_read(self):
        """Marks the notification as read."""
        self.is_read = True
        self.read_at = models.DateTimeField(auto_now=True)
        self.save()

    class Meta:
        unique_together = ('notification', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.notification.get_notification_type_display()} - {"Read" if self.is_read else "Unread"}'

class UserChatSummary(models.Model):
    """Stores the latest message and unread count for both single and group chats"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_summaries")
    chat_type = models.CharField(max_length=10, choices=[('single', 'Single Chat'), ('group', 'Group Chat')])
    # Can store either a single chat or a group chat message using GenericForeignKey
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    last_message = GenericForeignKey('content_type', 'object_id')
    last_message_sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="last_message_sender")
    last_message_time = models.DateTimeField()
    unread_count = models.PositiveIntegerField(default=0)  
    is_inactive = models.BooleanField(default=False) #marked true when a user left a group or was removed
    chat_group = models.ForeignKey(to=Group,on_delete=models.CASCADE,null=True,blank=True) #if group chat then only present
    other_user = models.ForeignKey(to=User,on_delete=models.CASCADE,null=True,blank=True,related_name="personal_chat_user")#user with whom personal chat going on
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id'] 

    def __str__(self):
        return f"{self.user.username} - {self.chat_type} - {self.unread_count} unread"

