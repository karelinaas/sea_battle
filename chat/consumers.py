import json

import redis
from channels.generic.websocket import AsyncWebsocketConsumer


r = redis.Redis(host='redis', port=6379, db=0)


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(ChatConsumer, self).__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None

        # TODO creds
        self.redis = r

    async def connect(self):
        if self.channel_layer.receive_count > 2:
            await self.close()

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_{0}'.format(self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        message = json.loads(text_data)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            message,
        )

    # Receive message from room group
    async def chat_message(self, event):
        text_data = json.dumps({
            'message': event['message'],
            'time': event['time'],
            'user': event['user'],
        })

        # Send message to WebSocket
        await self.send(text_data=text_data)

        self.redis.set(self.room_name + '_' + event['time'], text_data)


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(GameConsumer, self).__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None

        self.redis = r

    async def connect(self):
        if self.channel_layer.receive_count > 2:
            await self.close()

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_{0}'.format(self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            text_data_json
        )

    async def turn(self, event):
        me = event['from']
        another_player = 'player1' if me == 'player2' else 'player2'

        self.redis.set(self.room_name + '_turn', another_player)

        another_player_real_field = json.loads(self.redis.get('field_' + self.room_name + '_' + another_player))
        another_player_hidden_field = json.loads(self.redis.get('another_field_' + self.room_name + '_' + me))

        x = event['x']
        y = event['y']

        if another_player_real_field[x][y] == 0:
            another_player_real_field[x][y] = -2
            another_player_hidden_field[x][y] = -2
        elif another_player_real_field[x][y] == 1:
            another_player_real_field[x][y] = -1
            another_player_hidden_field[x][y] = -1

        self.redis.set('field_' + self.room_name + '_' + another_player, json.dumps(another_player_real_field))
        self.redis.set('another_field_' + self.room_name + '_' + me, json.dumps(another_player_hidden_field))

        await self.send(text_data=json.dumps({
            'from': me,
            'from_field': another_player_hidden_field,
            'to': another_player,
            'to_field': another_player_real_field,
        }))
