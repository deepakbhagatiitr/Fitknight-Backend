from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
from channels.exceptions import StopConsumer
from django.conf import settings

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            if self.scope["user"].is_anonymous:
                print("Anonymous user - closing connection")
                await self.close()
                return
                
            self.user = self.scope["user"]
            self.notification_group_name = f"notifications_{self.user.id}"
            
            print(f"\n=== WebSocket Connection ===")
            print(f"User: {self.user.username}")
            print(f"Group: {self.notification_group_name}")
            
            # Add to notification group
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"WebSocket accepted for {self.user.username}")
            
        except Exception as e:
            print(f"WebSocket connection error: {str(e)}")
            await self.close()

    async def notify(self, event):
        """Handle notification messages"""
        try:
            print(f"\n=== Sending WebSocket Notification ===")
            print(f"User: {self.user.username}")
            print(f"Event: {event}")
            
            # Send notification to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'data': event['data']
            }))
            print("Notification sent successfully")
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")

    async def disconnect(self, close_code):
        try:
            print(f"\n=== WebSocket Disconnection ===")
            print(f"User: {self.user.username}")
            print(f"Code: {close_code}")
            
            # Remove from notification group
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
        except Exception as e:
            print(f"Disconnect error: {str(e)}")

    async def ping_loop(self):
        """Send periodic pings to keep connection alive"""
        while True:
            try:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                await self.send(text_data=json.dumps({"type": "ping"}))
            except Exception:
                break

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "pong":
                return  # Ignore pong responses
            if 'current_chat_id' in data:
                self.current_chat = data['current_chat_id']
        except json.JSONDecodeError:
            pass
