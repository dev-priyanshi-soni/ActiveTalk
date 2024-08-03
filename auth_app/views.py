from django.shortcuts import render,redirect
from .models import User
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as auth_login, authenticate

def login_view(request):
    return render(request,'user/login.html')

def login(request):
    username=request.POST.get("username")
    password=request.POST.get("password")
    user_data=User.objects.filter(username=username)
    if not user_data.exists():
        return render(request,'user/signup.html',{'error_message':'User not exists. Please signup'})
    user = authenticate(request, username=username, password=password)
    if not user:
        return render(request,'user/login.html',{'error_message':'Incorrect Credentials'})
    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect("home")

def signup_view(request):
    return render(request,'user/signup.html')

def signup(request):  
    username=request.POST.get("username")
    password=request.POST.get("password")
    full_name=request.POST.get("full_name")
    user_data=User.objects.filter(username=username)
    if user_data.exists():
        return render(request,'user/login.html',{'error_message':"User already exists. Please login."})
    user=User.objects.create_user(username=username,password=password,full_name=full_name)
    return render(request,'user/login.html',{'error_message':"Signup successful. Please login."})

def signout(request):
    logout(request)
    return redirect("login_view")

