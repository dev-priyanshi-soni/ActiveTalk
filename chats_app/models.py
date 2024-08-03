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
    parent_message = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.SET_NULL)  # New field for replies

class Group(models.Model):   
    name=models.CharField(max_length=400,null=True,blank=True)
    users=models.ManyToManyField(User,through='GroupMemberships',related_name="group_users")
    created_at=models.DateTimeField(null=False)
    created_by= models.ForeignKey(to=User,on_delete=models.SET_NULL,null=True)

class GroupMemberships(models.Model):  
    user=models.ForeignKey(to=User,on_delete=models.SET_NULL,null=True)
    is_admin=models.BooleanField(default=False)
    group=models.ForeignKey(to=Group,on_delete=models.SET_NULL,null=True)

class GroupMessages(models.Model): 
    sender= models.ForeignKey(to=User,related_name='group_msg_sender_user' ,on_delete=models.SET_NULL,null=True)
    message=models.CharField(max_length=300,null=True,blank=True)
    sent_time=models.DateTimeField(null=False)
    file = models.FileField(upload_to='group_chat_files/', null=True, blank=True) 

class GroupMessageRead(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True,null=True)
    group_message = models.ForeignKey(GroupMessages, on_delete=models.CASCADE, db_index=True,null=True)
    read_at = models.DateTimeField(null=True,blank=True)

class Notification(models.Model):

    SINGLE_CHAT_MESSAGE = 'single_chat_message'
    GROUP_MESSAGE = 'group_message'
    GROUP_MEMBERSHIP_CHANGE = 'group_membership_change'

    NOTIFICATION_TYPES = [
        (SINGLE_CHAT_MESSAGE, 'New message in single chat'),
        (GROUP_MESSAGE, 'New message in group'),
        (GROUP_MEMBERSHIP_CHANGE, 'Group membership change'),
    ]
 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_received')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:  
        ordering = ['-timestamp']

    def __str__(self): 
        return f'{self.user.username} - {self.get_notification_type_display()}'