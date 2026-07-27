import json
import jdatetime
from datetime import date, timedelta, datetime
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import SupportRoom, SupportMessage

User = get_user_model()

from django.utils.translation import gettext as _

def format_date_display(dt):
    if not dt:
        return _("امروز")
    today = date.today()
    msg_date = dt.date() if isinstance(dt, datetime) else dt

    if msg_date == today:
        return _("امروز")
    elif msg_date == today - timedelta(days=1):
        return _("دیروز")
    else:
        try:
            j_dt = jdatetime.date.fromgregorian(date=msg_date)
            months = [_("فروردین"), _("اردیبهشت"), _("خرداد"), _("تیر"), _("مرداد"), _("شهریور"), _("مهر"), _("آبان"), _("آذر"), _("دی"), _("بهمن"), _("اسفند")]
            return f"{j_dt.day} {months[j_dt.month - 1]} {j_dt.year}"
        except Exception:
            return msg_date.strftime("%Y-%m-%d")

class SupportChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        room_id_kwarg = self.scope['url_route']['kwargs'].get('room_id')

        # If user is staff and requested specific room_id, join that room
        if self.user.is_staff and room_id_kwarg:
            self.room = await self.get_room_by_id(room_id_kwarg)
        else:
            # Regular user joins their own support room
            self.room = await self.get_or_create_user_room(self.user)

        if not self.room:
            await self.close()
            return

        self.room_id = int(self.room.id)
        self.room_group_name = f"support_room_{self.room_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Staff also joins support_operators group to get live updates for all rooms
        if self.user.is_staff:
            await self.channel_layer.group_add(
                "support_operators",
                self.channel_name
            )
            # Reset unread counter for admin when joining specific room
            await self.reset_unread_admin(self.room)

        await self.accept()

        # Send existing message history upon connection
        messages = await self.get_room_messages(self.room)
        await self.send_json({
            "type": "history",
            "messages": messages,
            "room_id": self.room_id
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        if hasattr(self, 'user') and self.user.is_staff:
            await self.channel_layer.group_discard(
                "support_operators",
                self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        event_type = content.get("type", "chat_message")

        # Handle typing indicator events
        if event_type == "typing":
            is_typing = content.get("is_typing", False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "is_typing": is_typing,
                    "sender_id": self.user.id,
                    "is_operator": self.user.is_staff,
                    "room_id": self.room_id
                }
            )
            return

        # Handle sending chat messages
        msg_text = content.get("message", "").strip()
        if not msg_text:
            return

        is_operator = self.user.is_staff
        saved_msg = await self.save_message(self.room, self.user, msg_text, is_operator)

        payload = {
            "type": "chat_message",
            "message": {
                "id": saved_msg['id'],
                "sender_id": self.user.id,
                "sender_name": self.user.get_full_name() or self.user.username,
                "sender_avatar": self.get_avatar_url(self.user, is_operator),
                "content": saved_msg['content'],
                "is_operator": is_operator,
                "created_at": saved_msg['created_at'],
                "date_display": saved_msg['date_display'],
                "room_id": self.room_id,
                "user_username": self.room.user.username,
                "user_display_name": self.room.user.get_full_name() or self.room.user.username,
            }
        }

        # Broadcast message to the specific chat room
        await self.channel_layer.group_send(
            self.room_group_name,
            payload
        )

        # Notify all support operators for room list updates & badges
        await self.channel_layer.group_send(
            "support_operators",
            payload
        )

    async def chat_message(self, event):
        await self.send_json(event)

    async def typing_status(self, event):
        # Do not bounce typing event back to the sender
        if event.get("sender_id") != self.user.id:
            await self.send_json(event)

    def get_avatar_url(self, user, is_operator):
        if hasattr(user, 'avatar') and user.avatar:
            return user.avatar.url
        
        name = user.get_full_name() or user.username
        bg = "3B0709" if is_operator else "DD0202"
        return f"https://ui-avatars.com/api/?name={name}&background={bg}&color=fff"

    @database_sync_to_async
    def get_or_create_user_room(self, user):
        room, _ = SupportRoom.objects.get_or_create(user=user)
        return room

    @database_sync_to_async
    def get_room_by_id(self, room_id):
        try:
            return SupportRoom.objects.get(id=room_id)
        except (SupportRoom.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def reset_unread_admin(self, room):
        room.unread_by_admin = 0
        room.save(update_fields=['unread_by_admin'])

    @database_sync_to_async
    def get_room_messages(self, room):
        msgs = room.messages.select_related('sender').all()[:100]
        result = []
        for m in msgs:
            if hasattr(m.sender, 'avatar') and m.sender.avatar:
                avatar = m.sender.avatar.url
            else:
                name = m.sender.get_full_name() or m.sender.username
                bg = "3B0709" if m.is_operator else "DD0202"
                avatar = f"https://ui-avatars.com/api/?name={name}&background={bg}&color=fff"

            result.append({
                "id": m.id,
                "sender_id": m.sender.id,
                "sender_name": m.sender.get_full_name() or m.sender.username,
                "sender_avatar": avatar,
                "content": m.content,
                "attachment_url": m.attachment.url if m.attachment else None,
                "attachment_name": m.attachment_name,
                "attachment_type": m.attachment_type,
                "is_operator": m.is_operator,
                "created_at": m.created_at.strftime("%H:%M"),
                "date_display": format_date_display(m.created_at),
                "room_id": room.id
            })
        return result

    @database_sync_to_async
    def save_message(self, room, sender, content, is_operator):
        msg = SupportMessage.objects.create(
            room=room,
            sender=sender,
            content=content,
            is_operator=is_operator
        )
        if not is_operator:
            room.unread_by_admin += 1
        else:
            room.unread_by_user += 1
        room.save()
        return {
            "id": msg.id,
            "content": msg.content,
            "created_at": msg.created_at.strftime("%H:%M"),
            "date_display": format_date_display(msg.created_at)
        }
