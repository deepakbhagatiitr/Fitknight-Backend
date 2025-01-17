from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            if self.scope["user"].is_anonymous:
                print("Anonymous user - closing connection")
                await self.close()
                return
                
            self.user = self.scope["user"]
            self.notification_group_name = f"notifications_{self.user.id}"
            
            print(f"User {self.user.username} connecting to {self.notification_group_name}")
            
            # Join notification group
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"WebSocket connected for user {self.user.username}")
            
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Only try to leave group if user was set during connect
            if hasattr(self, 'user') and hasattr(self, 'notification_group_name'):
                # Leave notification group
                await self.channel_layer.group_discard(
                    self.notification_group_name,
                    self.channel_name
                )
                print(f"WebSocket disconnected for user {self.user.username}")
        except Exception as e:
            print(f"Disconnect error: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if 'current_chat_id' in data:
                self.current_chat = data['current_chat_id']
        except json.JSONDecodeError:
            pass

    async def notify(self, event):
        try:
            if not hasattr(self, 'user'):
                print("No user found for notification")
                return
                
            notification_data = event['data']
            print(f"Sending notification to {self.user.username}")
            print("Notification data:", notification_data)
            
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'data': notification_data
            }))
            print(f"Notification sent to {self.user.username}")
            
        except Exception as e:
            print(f"Error in notify: {str(e)}") 