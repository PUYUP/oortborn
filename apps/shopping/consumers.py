import json
from channels.generic.websocket import AsyncWebsocketConsumer


class BasketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.basket_uuid = self.scope['url_route']['kwargs']['basket_uuid']
        self.basket_group = 'basket_%s' % self.basket_uuid

        if self.scope['user'].is_anonymous:
            # Reject the connection
            await self.close()
        else:
            # Accept connection
            # Join room group
            await self.channel_layer.group_add(
                self.basket_group,
                self.channel_name
            )

            await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.basket_group,
            self.channel_name
        )

    # Receive entry from WebSocket
    async def receive(self, text_data):
        data_json = json.loads(text_data)
        entry = data_json['entry']

        # Send entry to room group
        await self.channel_layer.group_send(
            self.basket_group,
            {
                'type': 'basket_entry_handler', # function handler
                'entry': entry
            }
        )

    # Receive entry from room group
    async def basket_entry_handler(self, event):
        entry = event['entry']

        # Send entry to WebSocket
        await self.send(text_data=json.dumps({
            'entry': entry
        }))
