from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, Group, ChatRoom, ChatMessage
from .serializers import NotificationSerializer

def send_notification(user_id, notification_type, title, message, related_object_id=None):
    try:
        print(f"\n=== Creating Notification ===")
        print(f"User ID: {user_id}")
        print(f"Type: {notification_type}")
        print(f"Message: {message}")
        
        # Create notification
        notification = Notification.objects.create(
            recipient_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_id=related_object_id
        )
        
        # Get channel layer
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("Error: Could not get channel layer")
            return
            
        # Send to WebSocket
        group_name = f"notifications_{user_id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notify",
                "data": NotificationSerializer(notification).data
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
    try:
        group = Group.objects.get(id=group_id)
        
        # Only send notification to the organizer
        if group.organizer.user.id == organizer_id:
            message = f"{requester_name} wants to join your group {group.name}"
            
            send_notification(
                user_id=organizer_id,
                notification_type='join_request',
                title='New Join Request',
                message=message,
                related_object_id=group_id
            )
            print(f"Join request notification sent to organizer {organizer_id}")
        else:
            print(f"Skipping notification - user {organizer_id} is not the organizer")
            
    except Group.DoesNotExist:
        print(f"Error: Group {group_id} not found")
    except Exception as e:
        print(f"Error sending join request notification: {str(e)}")

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

def notify_new_message(user_id, chat_id, sender_name, message_content):
    """Send group chat message notification"""
    try:
        chat_room = ChatRoom.objects.get(id=chat_id)
        # Format the message as "sender: message"
        message = f"{sender_name}: {message_content}"
            
        send_notification(
            user_id=user_id,
            notification_type='group_chat',
            title=f'New message in {chat_room.group.name}',
            message=message,  # This will show as "john: Hello everyone!"
            related_object_id=chat_id
        )
        print(f"Chat notification sent to user {user_id}")
    except ChatRoom.DoesNotExist:
        print(f"Error: Chat room {chat_id} not found")
    except Exception as e:
        print(f"Error sending chat notification: {str(e)}") 
