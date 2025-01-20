from django.urls import re_path
from . import consumers
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

websocket_urlpatterns = [
    re_path(r'^ws/notifications/?$', consumers.NotificationConsumer.as_asgi()),
] 

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            query_string = scope.get('query_string', b'').decode()
            token = dict(x.split('=') for x in query_string.split('&')).get('token', None)
            
            if token:
                # get user from token
                user = await self.get_user_from_token(token)
                scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
                
        except Exception as e:
            print(f"Auth error: {str(e)}")
            scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()

TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner)) 