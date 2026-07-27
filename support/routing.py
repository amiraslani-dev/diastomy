from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/support/chat/$', consumers.SupportChatConsumer.as_asgi()),
    re_path(r'ws/support/chat/(?P<room_id>\d+)/$', consumers.SupportChatConsumer.as_asgi()),
]
