# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sender = self.scope['url_route']['kwargs']['sender']
        self.recipient = self.scope['url_route']['kwargs']['recipient']
        self.room_name = f'chat_{min(self.sender, self.recipient)}_{max(self.sender, self.recipient)}'
        
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Save message to database
        from .models import Message
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        sender = await User.objects.aget(username=self.sender)
        recipient = await User.objects.aget(username=self.recipient)
        
        msg = await Message.objects.acreate(
            sender=sender,
            recipient=recipient,
            content=message['content']
        )
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(msg.id),
                    'sender': self.sender,
                    'content': message['content'],
                    'timestamp': msg.timestamp.isoformat(),
                    'isCurrentUser': False
                }
            }
        )

    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))