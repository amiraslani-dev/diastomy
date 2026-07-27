import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import SupportRoom, SupportMessage
from .consumers import format_date_display
from core.models import DashboardSetting

@login_required
def support_view(request):
    room, _ = SupportRoom.objects.get_or_create(user=request.user)
    setting = DashboardSetting.objects.first()
    support_avatars = setting.support_avatars.all() if setting else []
    return render(request, 'support/support.html', {
        'active_tab': 'support',
        'room': room,
        'support_avatars': support_avatars,
    })

@staff_member_required
def operator_chat_view(request):
    # Only list rooms that have at least one message (sent by user or operator)
    rooms = SupportRoom.objects.filter(messages__isnull=False).distinct().select_related('user').order_by('-updated_at')
    rooms_data = []
    for r in rooms:
        user_name = r.user.get_full_name() or r.user.username
        if hasattr(r.user, 'avatar') and r.user.avatar:
            avatar = r.user.avatar.url
        else:
            avatar = f"https://ui-avatars.com/api/?name={user_name}&background=DD0202&color=fff"

        rooms_data.append({
            "id": r.id,
            "username": r.user.username,
            "display_name": user_name,
            "avatar": avatar,
            "unread_by_admin": r.unread_by_admin,
            "updated_at": r.updated_at.strftime("%H:%M")
        })
    return render(request, 'support/operator_chat.html', {
        'rooms': rooms,
        'rooms_data_json': json.dumps(rooms_data, ensure_ascii=False),
    })

@login_required
@require_POST
def upload_attachment_view(request):
    file_obj = request.FILES.get('file')
    room_id = request.POST.get('room_id')
    content_text = request.POST.get('content', '').strip()

    if not file_obj:
        return JsonResponse({'error': 'هیچ فایلی انتخاب نشده است.'}, status=400)

    if request.user.is_staff and room_id:
        try:
            room = SupportRoom.objects.get(id=room_id)
        except SupportRoom.DoesNotExist:
            return JsonResponse({'error': 'اتاق پشتیبانی یافت نشد.'}, status=404)
    else:
        room, _ = SupportRoom.objects.get_or_create(user=request.user)

    is_operator = request.user.is_staff

    msg = SupportMessage.objects.create(
        room=room,
        sender=request.user,
        content=content_text,
        attachment=file_obj,
        is_operator=is_operator
    )

    if not is_operator:
        room.unread_by_admin += 1
    else:
        room.unread_by_user += 1
    room.save()

    name = request.user.get_full_name() or request.user.username
    bg = "3B0709" if is_operator else "DD0202"
    avatar = request.user.avatar.url if (hasattr(request.user, 'avatar') and request.user.avatar) else f"https://ui-avatars.com/api/?name={name}&background={bg}&color=fff"

    msg_data = {
        "id": msg.id,
        "sender_id": request.user.id,
        "sender_name": name,
        "sender_avatar": avatar,
        "content": msg.content,
        "attachment_url": msg.attachment.url if msg.attachment else None,
        "attachment_name": msg.attachment_name,
        "attachment_type": msg.attachment_type,
        "is_operator": is_operator,
        "created_at": msg.created_at.strftime("%H:%M"),
        "date_display": format_date_display(msg.created_at),
        "room_id": room.id,
        "user_username": room.user.username,
        "user_display_name": room.user.get_full_name() or room.user.username,
    }

    # Broadcast via Channel Layer to WebSocket clients
    channel_layer = get_channel_layer()
    payload = {
        "type": "chat_message",
        "message": msg_data
    }

    async_to_sync(channel_layer.group_send)(f"support_room_{room.id}", payload)
    async_to_sync(channel_layer.group_send)("support_operators", payload)

    return JsonResponse({'status': 'ok', 'message': msg_data})