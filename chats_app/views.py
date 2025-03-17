from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from auth_app.models import User
from chats_app.models import *
from django.db.models import *
from django.core.paginator import Paginator
from .serializer import ChatModelSerializer,GroupChatsModelSerializer,GroupSerializer,GroupMembershipsSerializer,GroupMembershipsDataSerializer,UserChatSummarySerializer,NotificationReadStatusSerializer
import json
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .utilities import send_event_for_group_member_removal,check_user_group_membership,create_event_for_deleted_group_message,create_event_for_deleted_personal_chat_message
from django.core.paginator import EmptyPage
import traceback
from auth_app.serializers import UserSerializer

def home(request):
    if request.user.is_authenticated:
        delivered_at=timezone.now()
        user=request.user
        # chats_data = UserChatSummary.objects.filter(user=request.user)
        # serialized_chats_data = UserChatSummarySerializer(chats_data, many=True)
        # user_ids = ChatModel.objects.filter(
        #     Q(sender=user) | Q(receiver=user)
        # ).values_list('sender', 'receiver').distinct()[:10]
        # friend_user_ids = {user_id for user_id_tuple in user_ids for user_id in user_id_tuple if user_id and user_id != user.id}
        # friends_data = User.objects.filter(id__in=friend_user_ids)
        # users_data=User.objects.all().exclude(id__in=friend_user_ids).exclude(id=user.id)
        # groups_data=Group.objects.filter(groupmemberships__user=request.user)
        messages_not_delivered = GroupMessageRead.objects.filter(user_id=request.user,delivered_time=None,read_at=None)
        #this will fetch those messages which were sent in any of groups he has joined when he was offline. we need to mark them delivered now as user became online now.
        messages_not_delivered.update(delivered_time=delivered_at)
        return render(request,'user/chats_home.html')
    return render(request,'user/login.html')

def chats_page(request,id):
    if request.user.is_authenticated:
        user=request.user
        delivered_at = timezone.now()
        content_type = ContentType.objects.get_for_model(ChatModel)
        messages = ChatModel.objects.filter(
            (Q(sender=user.id) & Q(receiver=id)) | (Q(sender=id) & Q(receiver=user.id))
        ).order_by('-id')  
        paginator = Paginator(messages, 10)  
        page_number = request.GET.get('page', 1)  
        page_messages = paginator.get_page(page_number)  
        other_user = get_object_or_404(User, id=id)
        page_messages=list(page_messages)[::-1]
        serialized_data = ChatModelSerializer(page_messages, many=True)
        return render(request, 'user/chatting_page.html', {
            'page_messages': serialized_data.data,
            'other_user': other_user,
            'receiver_id':id
        })
    return render(request,'user/login.html')

def get_previous_messages(request,sender_id,receiver_id,page):
    try:
        if request.user.is_authenticated:
            messages = ChatModel.objects.filter(
                (Q(sender=sender_id) & Q(receiver=receiver_id)) | (Q(sender=receiver_id) & Q(receiver=sender_id))
            ).order_by('-id')  
            paginator = Paginator(messages, 10)  
            page_number = page
            if paginator.num_pages < page_number:
                return JsonResponse({'page_messages': list(),'Error':'No Data FOund','Status':'No Data Found'})
            page_messages = paginator.get_page(page_number)  
            serialized_data = ChatModelSerializer(page_messages, many=True)
            return JsonResponse({'page_messages': serialized_data.data,'Error':'NA','Status':'Success'})
        return JsonResponse({'page_messages': list(),'Error':'Auth Error','Status':'Auth Error'})
    except Exception as ex:
        return JsonResponse({'page_messages': list(),'Error':'Some Error Occurred','Status':str(ex)})


def reply_to_message(request,sender_id,receiver_id,message_id):
    try:
        if request.user.is_authenticated:
            message=ChatModel.objects.get(id=message_id)
            new_message=ChatModel.objects.create(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message=request.POST.get('message'),
                parent_message=message
            )
            serialized_data = ChatModelSerializer(new_message)
            return JsonResponse({'page_messages': serialized_data.data,'Error':'NA','Status':'Success'})
        return JsonResponse({'page_messages': list(),'Error':'Auth Error','Status':'Auth Error'})
    except Exception as ex:
        return JsonResponse({'page_messages': list(),'Error':'Some Error Occurred','Status':str(ex)})
    
@login_required
def join_group(request,group_id):
    try:
        if request.method=='POST':
            group_rec=Group.objects.filter(id=group_id)
            if not group_rec.exists():
                return JsonResponse({'Error':"group not exists",'Status':"group not found"})
            group_rec=group_rec.last()
            group_member=GroupMemberships.objects.filter(group=group_rec,user=request.user)
            if group_member.exists():
                return JsonResponse({'Error':"Already in group",'Status':"Already in group"})
            obj=GroupMemberships.objects.create(group=group_rec,user=request.user)
            return JsonResponse({'Error':"NA","Status":"Success"})
        return render(request,'user/joining_group_page.html',{'group_id':group_id})
    except Exception as ex:
        return JsonResponse({'Error':'Some Error Occurred','Status':str(ex)})

@login_required
def create_group(request):
    try:
        if request.method=='POST':
            req_body=request.body.decode("utf-8")
            body=json.loads(req_body)
            group_name=body.get("name")
            group_rec=Group.objects.filter(name=group_name)
            if  group_rec.exists():
                return JsonResponse({'Error':"group already exists",'Status':"group already exists"})
            group_rec=Group.objects.create(name=group_name)
            group_member_rec=GroupMemberships.objects.create(group=group_rec,is_admin=True,user=request.user)
            return JsonResponse({'Error':"NA","Status":"Success"})
        return JsonResponse({'Error':"Method Error","Status":"method Error"})
    except Exception as ex:
        return JsonResponse({'Error':'Some Error Occurred','Status':str(ex)})

@login_required
def group_chat(request,group_id):
    is_group_member,error_message = check_user_group_membership(group_id,request.user.id)
    if not is_group_member:
        return render(request,'user/group_chats.html',{'error_message':error_message})
    group_data=Group.objects.filter(pk=group_id)
    if not group_data.exists():
        return redirect("home")
    group_data=group_data.last()
    serialized_group_data=GroupSerializer(group_data).data
    group_admin_id=None
    group_admin_name=None
    group_admin=GroupMemberships.objects.filter(group__id=group_id,is_admin=True)
    if group_admin.exists():
        group_admin=group_admin.last()
        group_admin_id=group_admin.user.id
        group_admin_name=group_admin.user.full_name
    unread_msg_count=0
    unread_msg_start_id=None
    messages_unread_by_user=GroupMessageRead.objects.filter(group_message__group__id=group_id,user_id=request.user,delivered_time__isnull=False,read_at=None).order_by('id')
    remaining_needed=0
    need_to_reverse=False
    if messages_unread_by_user.exists():
        unread_msg_count = messages_unread_by_user.count()
        messages_unread_list=[x.group_message for x in messages_unread_by_user][:10]
        remaining_needed = 10 - len(messages_unread_list)
        if remaining_needed > 0:#do
            messages_previous = GroupMessages.objects.filter(
                group=group_data,
                id__lt=messages_unread_list[0].id
            ).order_by('-id')[0:remaining_needed]
            unread_msg_start_id = list(messages_unread_list)[0].id
            messages_combined = list(messages_unread_list) + list(messages_previous)
        else:
            unread_msg_start_id = messages_unread_list[0].id
            messages_combined = messages_unread_list
        messages_combined = sorted(messages_combined, key=lambda x: x.id)
        paginator = Paginator(messages_combined, 10)
    else:
        need_to_reverse=True
        group_chat_messages = GroupMessages.objects.filter(
            group=group_data
        ).order_by('-id')
        paginator = Paginator(group_chat_messages, 10)
       
    page_number = request.GET.get('page', 1)  
    page_messages = paginator.get_page(page_number)  
    if need_to_reverse:
        page_messages=list(page_messages)[::-1]
    serialized_chats_data = GroupChatsModelSerializer(page_messages, many=True,context={'user':request.user})
    return render(request,'user/group_chats.html',{'unread_msg_count':unread_msg_count,'unread_msg_start_id':unread_msg_start_id,'group_chat_messages':serialized_chats_data.data,'group':serialized_group_data,'group_admin':group_admin_id,'group_admin_name':group_admin_name})

def get_previous_group_chats_messages(request,group_id,page,last_message_id):
    try:
        #we use last_message_id to get last message id of previous page so that we can get messages before that id.
        if request.user.is_authenticated:
            group_data=Group.objects.filter(pk=group_id)
            if not group_data.exists():
                return JsonResponse({'page_messages': list(),'Error':'group not found','Status':'group not found'})
            group_data=group_data.last()
            group_chat_messages=GroupMessages.objects.filter(group=group_data,id__lt=last_message_id).order_by('-id')  
            paginator = Paginator(group_chat_messages, 10)  
            page_number = 1
            if page>paginator.num_pages:
                return JsonResponse({'page_messages': list(),'Error':'NA','Status':'Success'})
            page_messages = paginator.get_page(page_number)  
            #page_messages=list(page_messages)[::-1]
            serialized_data = GroupChatsModelSerializer(page_messages, many=True,context={'user':request.user})
            return JsonResponse({'page_messages': serialized_data.data,'Error':'NA','Status':'Success'})
        return JsonResponse({'page_messages': list(),'Error':'Auth Error','Status':'Auth Error'})
    except Exception as ex:
        return JsonResponse({'page_messages': list(),'Error':'Some Error Occurred','Status':str(ex)})
    

def get_next_group_chats_messages(request,group_id,page,curr_msg_id):
    try:
        #this api is called when user scrolls down. so wew use curr_msg_id to get messages after the last id message he saw.
        if request.user.is_authenticated:
            group_data=Group.objects.filter(pk=group_id)
            if not group_data.exists():
                return JsonResponse({'page_messages': list(),'Error':'group not found','Status':'group not found'})
            group_data=group_data.last()
            group_chat_messages=GroupMessages.objects.filter(group=group_data,id__gt=curr_msg_id).order_by('-id')  
            paginator = Paginator(group_chat_messages, 10)  
            page_number = page
            if page>paginator.num_pages:
                return JsonResponse({'page_messages': list(),'Error':'NA','Status':'Success'})
            page_messages = paginator.get_page(page_number)  
            page_messages=list(page_messages)[::-1]
            serialized_data = GroupChatsModelSerializer(page_messages, many=True,context={'user':request.user})
            return JsonResponse({'page_messages': serialized_data.data,'Error':'NA','Status':'Success'})
        return JsonResponse({'page_messages': list(),'Error':'Auth Error','Status':'Auth Error'})
    except Exception as ex:
        return JsonResponse({'page_messages': list(),'Error':'Some Error Occurred','Status':str(ex)})
    

def get_read_statuses(request,group_id,message_id):
    try:
        if request.method=='GET':
            message_read_statuses=GroupMemberships.objects.filter(group__id=group_id).exclude(user=request.user).annotate(
                read_at=Subquery(
                    GroupMessageRead.objects.filter(group_message__id=message_id,
                                                    user_id=OuterRef('user'),

                                                    
                                                    ).values('read_at')[:1]

                ),
                delivered_at=Subquery(
                     GroupMessageRead.objects.filter(group_message__id=message_id,
                                                    user_id=OuterRef('user'),

                                                    
                                                    ).values('delivered_time')[:1]
                )
            )
            serialized_data = GroupMembershipsSerializer(message_read_statuses, many=True) 

            return JsonResponse({'Error':'NA','Status':serialized_data.data})
        return JsonResponse({'Error':'Method Error','Status':'Method Error'})
    except Exception as ex:
        return JsonResponse({'Error':'Some Error Occurred','Status':str(ex)})
    
@login_required
def get_group_members(request,group_id):
    try:
        if request.method=='GET':
            group_data=Group.objects.filter(pk=group_id)
            if not group_data.exists():
                return JsonResponse({'Error':"Group not found",'Status':"Group not found"})
            group_data=group_data.last()
            group_members=GroupMemberships.objects.filter(group=group_data)
            serialized_data = GroupMembershipsDataSerializer(group_members, many=True) 
            return JsonResponse({'Error':'NA','Status':serialized_data.data})
        return JsonResponse({'Error':'Method Error','Status':'Method Error  '})
    except Exception as ex:
        return JsonResponse({'Error':'Some Error Occurred','Status':str(ex)})

@login_required
def remove_group_member(request,group_id,group_member_id):
    try:
        if request.method=='DELETE':
            if not group_id or not group_member_id:
                return JsonResponse({'Error':'Missing Fields','Status':'Missing Fields'})
            group_data=Group.objects.filter(pk=group_id)
            if not group_data.exists():
                return JsonResponse({'Error':"Group not found",'Status':"Group not found"})
            group_data=group_data.last()
            user_is_group_admin=GroupMemberships.objects.filter(group=group_data,user__id=request.user.id,is_admin=True)
            if not user_is_group_admin:
                return JsonResponse({'Error':'UnAuthorized','Status':'Only Admin can remove participants'})
            group_member_to_delete=GroupMemberships.objects.filter(group=group_data,user__id=group_member_id)
            if group_member_to_delete.exists():
                group_member_to_delete=group_member_to_delete.last()
                send_event_for_group_member_removal(group_id,group_member_to_delete,request.user)
                group_member_to_delete.delete()
                # Mark chat summary as inactive for removed user
                UserChatSummary.objects.filter(
                    user_id=group_member_id,
                    chat_type='group', 
                ).update(is_inactive=True)
                return JsonResponse({'Error':'NA','Status':"Success"})
            return JsonResponse({'Error':"Group Member not found",'Status':"Group Member not found"})
        return JsonResponse({'Error':'Method Error','Status':'Method Error  '})
    except Exception as ex:
        return JsonResponse({'Error':'Some Error Occurred','Status':str(ex)})
    
@login_required
def get_users(request):
    try:
        if request.method != 'GET':
            return JsonResponse({'Error': 'Method Error', 'Status': 'Only GET method allowed'})

        search_query = request.GET.get('search', '').strip()
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 10)

        try:
            page = int(page)
            per_page = int(per_page)
            if page < 1 or per_page < 1:
                raise ValueError
        except ValueError:
            return JsonResponse({'Error': 'Invalid pagination parameters', 'Status': 'Page and per_page must be positive integers'})

        # Get IDs of users who have chatted with current user
        chatted_user_ids = ChatModel.objects.filter(
            Q(sender=request.user.id) | Q(receiver=request.user.id)
        ).values_list('sender', 'receiver').distinct()
        
        # Flatten and remove current user's ID
        chatted_users = {uid for pair in chatted_user_ids for uid in pair if uid != request.user.id}
        
        # Exclude both chatted users and current user
        users = User.objects.exclude(id=request.user.id).exclude(id__in=chatted_users).exclude(is_superuser=True)

        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(full_name__icontains=search_query)
            )

        paginator = Paginator(users, per_page)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            return JsonResponse({'Error': 'Page not found', 'Status': 'The requested page does not exist'})

        users_data = UserSerializer(page_obj.object_list,many=True)

        response_data = {
            'Error': 'NA',
            'Status': 'Success',
            'data': {
                'users': users_data.data,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'total_users': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }

        return JsonResponse(response_data)

    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({'Error': 'Some Error Occurred', 'Status': str(ex)})

@login_required
def get_chat_summaries(request):
    try:
        if request.method != 'GET':
            return JsonResponse({'Error': 'Method Error', 'Status': 'Only GET method allowed'})

        # Get all chat summaries for the user ordered by last message time
        chat_summaries = UserChatSummary.objects.filter(
            user=request.user,
            is_inactive=False
        ).order_by('-last_message_time')

        # Paginate results
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 10)

        try:
            page = int(page)
            per_page = int(per_page)
            if page < 1 or per_page < 1:
                raise ValueError
        except ValueError:
            return JsonResponse({
                'Error': 'Invalid pagination parameters',
                'Status': 'Page and per_page must be positive integers'
            })

        paginator = Paginator(chat_summaries, per_page)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            return JsonResponse({
                'Error': 'Page not found',
                'Status': 'The requested page does not exist'
            })

        summaries_data = UserChatSummarySerializer(page_obj.object_list,many=True)

        response_data = {
            'Error': 'NA',
            'Status': 'Success',
            'data': {
                'summaries': summaries_data.data,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'total_summaries': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }

        return JsonResponse(response_data)

    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({'Error': 'Some Error Occurred', 'Status': str(ex)})

@login_required
def get_newly_joined_groups(request):
    '''
    This view sends groups where no chat has been initiated.
    '''
    try:
        search_query = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        groups = Group.objects.filter(
            users=request.user
        ).exclude(
            id__in=GroupMessages.objects.values('group')
        )
        if search_query:
            groups = groups.filter(name__icontains=search_query)
        groups = groups.order_by('-created_at')
        paginator = Paginator(groups, per_page)
        page_obj = paginator.get_page(page)
        groups_data = GroupSerializer(page_obj.object_list,many=True)
        response_data = {
            'Error': 'NA', 
            'Status': 'Success',
            'data': {
                'groups': groups_data.data,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'total_groups': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }
        return JsonResponse(response_data)
    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({
            'Error': 'Some Error Occurred',
            'Status': str(ex)
        }, status=500)

@login_required
def get_notifications(request):
    '''
    This view returns notifications for the logged in user.
    '''
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))

        notification_statuses = NotificationReadStatus.objects.filter(
            user=request.user
        ).select_related(
            'notification'
        ).order_by(
            '-notification__timestamp'
        )

        paginator = Paginator(notification_statuses, per_page)
        page_obj = paginator.get_page(page)
        
        notifications_data = NotificationReadStatusSerializer(
            page_obj.object_list,
            many=True
        )

        response_data = {
            'Error': 'NA',
            'Status': 'Success', 
            'data': {
                'notifications': notifications_data.data,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'total_notifications': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }

        return JsonResponse(response_data)

    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({
            'Error': 'Some Error Occurred',
            'Status': str(ex)
        }, status=500)

@login_required
def mark_notification_read(request):
    '''
    This view marks notifications as read for the logged in user.
    '''
    try:
        if request.method != 'PUT':
            return JsonResponse({
                'Error': 'Method not allowed',
                'Status': 'Failed'
            }, status=405)

        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        if not notification_ids:
            return JsonResponse({
                'Error': 'No notification IDs provided',
                'Status': 'Failed'
            }, status=400)

        NotificationReadStatus.objects.filter(
            user=request.user,
            notification_id__in=notification_ids,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return JsonResponse({
            'Error': 'NA',
            'Status': 'Success',
            'message': 'Notifications marked as read successfully'
        })

    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({
            'Error': 'Some Error Occurred',
            'Status': str(ex)
        }, status=500)

@login_required
def delete_group_message(request,group_message_id):
    '''
    This view handles deletion of group messages. Messages can only be deleted by the sender within 1 minute of sending.
    '''
    try:
        if request.method != 'DELETE':
            return JsonResponse({
                'Error': 'Method not allowed', 
                'Status': 'Failed'
            }, status=405)

        if not group_message_id:
            return JsonResponse({
                'Error': 'Message ID is required',
                'Status': 'Failed'
            }, status=400)

        message = GroupMessages.objects.filter(
            id=group_message_id,
            sender=request.user,
            is_deleted=False
        ).first()

        if not message:
            return JsonResponse({
                'Error': 'Message not found or you are not authorized to delete it',
                'Status': 'Failed'
            }, status=404)

        time_diff = timezone.now() - message.sent_time
        if time_diff.total_seconds() > 60:
            return JsonResponse({
                'Error': 'Messages can only be deleted within 1 minute of sending',
                'Status': 'Failed'
            }, status=400)

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.message = 'This message was deleted'
        message.save()

        create_event_for_deleted_group_message(group_msg_rec=message)

        return JsonResponse({
            'Error': 'NA',
            'Status': 'Success',
            'message': 'Message deleted successfully'
        })

    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({
            'Error': 'Some Error Occurred',
            'Status': str(ex)
        }, status=500)
    

@login_required
def delete_personal_chat_message(request,chat_message_id):
    '''
    This view handles deletion of personal chat messages. Messages can only be deleted by the sender within 1 minute of sending.
    '''
    try:
        if request.method != 'DELETE':
            return JsonResponse({
                'Error': 'Method not allowed', 
                'Status': 'Failed'
            }, status=405)

        if not chat_message_id:
            return JsonResponse({
                'Error': 'Message ID is required',
                'Status': 'Failed'
            }, status=400)

        message = ChatModel.objects.filter(
            id=chat_message_id,
            is_deleted=False
        ).first()

        if not message:
            return JsonResponse({
                'Error': 'Message not found or you are not authorized to delete it',
                'Status': 'Failed'
            }, status=404)

        time_diff = timezone.now() - message.sent_time
        if time_diff.total_seconds() > 60:
            return JsonResponse({
                'Error': 'Messages can only be deleted within 1 minute of sending',
                'Status': 'Failed'
            }, status=400)

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.message = 'This message was deleted'
        message.save()

        create_event_for_deleted_personal_chat_message(chat_message_rec=message)

        return JsonResponse({
            'Error': 'NA',
            'Status': 'Success',
            'message': 'Message deleted successfully'
        })

    except Exception as ex:
        traceback.print_exc()
        return JsonResponse({
            'Error': 'Some Error Occurred',
            'Status': str(ex)
        }, status=500)