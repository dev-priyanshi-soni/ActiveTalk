from django.urls import path
from . import views

urlpatterns = [
    path("login",views.login,name="login"),
    path("signup",views.signup,name="signup"),
    path('login_view',views.login_view,name='login_view'),
    path('signup_view',views.signup_view,name='signup_view'),
    path('signout',views.signout,name='signout'),
]