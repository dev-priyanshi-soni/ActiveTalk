from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from auth_app.models import User
from chats_app.models import *
from django.db.models import *
from django.core.paginator import Paginator
from .serializer import ChatModelSerializer
import json
from django.contrib.auth.decorators import login_required

def home(request):
    if request.user.is_authenticated:
        user=request.user
        user_ids = ChatModel.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values_list('sender', 'receiver').distinct()
        friend_user_ids = {user_id for user_id_tuple in user_ids for user_id in user_id_tuple if user_id and user_id != user.id}
        friends_data = User.objects.filter(id__in=friend_user_ids)
        users_data=User.objects.all().exclude(id__in=friend_user_ids).exclude(id=user.id)
        groups_data=Group.objects.filter(groupmemberships__user=request.user)
        return render(request,'user/chats_home.html',{'users_data':users_data,'friends_data':friends_data,'groups_data':groups_data})
    return render(request,'user/login.html')


def chats_page(request,id):
    if request.user.is_authenticated:
        user=request.user
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
        if request.method=='GET':
            group_rec=Group.objects.filter(id=group_id)
            if not group_rec.exists():
                return JsonResponse({'Error':"group not exists",'Status':"group not found"})
            group_rec=group_rec.last()
            group_member=GroupMemberships.objects.filter(group=group_rec,user=request.user)
            if group_member.exists():
                return JsonResponse({'Error':"Already in group",'Status':"Already in group"})
            obj=GroupMemberships.objects.create(group=group_rec,user=request.user)
            return JsonResponse({'Error':"NA","Status":"Success"})
        return JsonResponse({'Error':"Method Error","Status":"method Error"})
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
    # return render(request,'group_chats.html')
    group_data=Group.objects.filter(pk=group_id)
    if not group_data.exists():
        return redirect("home")

    group_data=group_data.last()
    group_chat_messages=GroupMessages.objects.filter(group=group_data)
    paginator = Paginator(group_chat_messages, 10)  
    page_number = request.GET.get('page', 1)  
    page_messages = paginator.get_page(page_number)  
    page_messages=list(page_messages)[::-1]
    serialized_data = ChatModelSerializer(page_messages, many=True)
    return render(request,'user/group_chats.html',{'group_chat_messages':serialized_data,'group':group_data})