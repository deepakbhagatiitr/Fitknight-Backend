from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
<<<<<<< HEAD
from .models import Notification, Group, ChatRoom, ChatMessage
=======
from .models import Notification
>>>>>>> 4630e8e33d3f6fe53a6b491e28f899d040835f12
from .serializers import NotificationSerializer

def send_notification(user_id, notification_type, title, message, related_object_id=None):
    print(f"\n=== Sending Notification ===")
    print(f"User ID: {user_id}")
    print(f"Type: {notification_type}")
    print(f"Message: {message}")
    
    try:
        # Create notification in database
        notification = Notification.objects.create(
            recipient_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_id=related_object_id
        )
        
        # Serialize notification
        serialized_data = NotificationSerializer(notification).data
        
        # Get channel layer
        channel_layer = get_channel_layer()
        
        # Send to WebSocket group
        group_name = f"notifications_{user_id}"
        print(f"Sending to group: {group_name}")
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notify",
                "data": serialized_data
            }
        )
        print("Notification sent successfully")
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")

# Utility functions for specific notification types
def notify_buddy_match(user_id, matched_buddy_id):
    send_notification(
        user_id=user_id,
        notification_type='buddy_match',
        title='New Buddy Match!',
        message=f'You have a new buddy match waiting for you!',
        related_object_id=matched_buddy_id
    )

def notify_group_suggestion(user_id, group_id):
    send_notification(
        user_id=user_id,
        notification_type='group_suggestion',
        title='Group Suggestion',
        message=f'We found a group that matches your interests!',
        related_object_id=group_id
    )

def notify_join_request(organizer_id, group_id, requester_name):
    """Send notification to group organizer about new join request"""
<<<<<<< HEAD
    # Get group name
    try:
        group = Group.objects.get(id=group_id)
        message = f"{requester_name} wants to join your group {group.name}"
        
        send_notification(
            user_id=organizer_id,
            notification_type='join_request',
            title='New Join Request',
            message=message,
            related_object_id=group_id
        )
    except Group.DoesNotExist:
        print(f"Error: Group {group_id} not found")
=======
    print(f"\n=== Sending Join Request Notification ===")
    print(f"To organizer: {organizer_id}")
    print(f"From user: {requester_name}")
    
    send_notification(
        user_id=organizer_id,
        notification_type='join_request',
        title='New Join Request',
        message=f'{requester_name} wants to join your group',
        related_object_id=group_id
    )
>>>>>>> 4630e8e33d3f6fe53a6b491e28f899d040835f12

def notify_group_chat(user_id, group_id):
    send_notification(
        user_id=user_id,
        notification_type='group_chat',
        title='New Group Message',
        message=f'You have a new message in your group chat',
        related_object_id=group_id
    )

def notify_request_response(user_id, group_id, accepted):
    """Send notification to user about their join request status"""
<<<<<<< HEAD
    try:
        group = Group.objects.get(id=group_id)
        status = "accepted" if accepted else "rejected"
        message = f"Your request to join group {group.name} was {status}"
        
        send_notification(
            user_id=user_id,
            notification_type='request_update',
            title=f'Join Request {status.title()}',
            message=message,
            related_object_id=group_id
        )
    except Group.DoesNotExist:
        print(f"Error: Group {group_id} not found")

def notify_new_message(user_id, chat_id, sender_name):
    """Send chat message notification"""
    try:
        chat_room = ChatRoom.objects.get(id=chat_id)
        # Get the last message for this chat
        last_message = ChatMessage.objects.filter(room=chat_room).last()
        
        if last_message:
            message = f"{sender_name}: {last_message.content}"
        else:
            message = f"New message from {sender_name}"
            
        send_notification(
            user_id=user_id,
            notification_type='group_chat',
            title='New Message',
            message=message,
            related_object_id=chat_id
        )
    except ChatRoom.DoesNotExist:
        print(f"Error: Chat room {chat_id} not found") 
=======
    status = "accepted" if accepted else "rejected"
    print(f"\n=== Sending Request Response Notification ===")
    print(f"To user: {user_id}")
    print(f"Status: {status}")
    
    send_notification(
        user_id=user_id,
        notification_type='request_update',
        title=f'Join Request {status.title()}',
        message=f'Your request to join the group was {status}',
        related_object_id=group_id
    )

def notify_new_message(user_id, chat_id, sender_name):
    send_notification(
        user_id=user_id,
        notification_type='group_chat',
        title='New Message',
        message=f'New message from {sender_name}',
        related_object_id=chat_id
    ) 
>>>>>>> 4630e8e33d3f6fe53a6b491e28f899d040835f12
