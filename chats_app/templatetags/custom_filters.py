from django import template
from django.utils import timezone
from django.db.models import Max
from auth_app.models import *
register = template.Library()
from chats_app.models import *
