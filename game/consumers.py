import json

import redis
from channels.generic.websocket import AsyncWebsocketConsumer

r = redis.Redis(host='redis', port=6379, db=0)


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(ChatConsumer, self).__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None

        self.redis = r

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_{0}'.format(self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

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
            'time_unix': event['time_unix'],
            'from': event['from'],
        })

        self.redis.set('chat_{0}_{1}'.format(self.room_name, event['time_unix']), text_data)

        # Send message to WebSocket
        await self.send(text_data=text_data)


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(GameConsumer, self).__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.turn_player = None

        self.redis = r

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_{0}'.format(self.room_name)
        self.turn_player = self.redis.get('{0}_turn'.format(self.room_group_name))

        if not self.turn_player:
            self.turn_player = 'player1'
            self.redis.set('{0}_turn'.format(self.room_group_name), self.turn_player)
        else:
            self.turn_player = self.turn_player.decode('ascii')

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        # Send message to room group
        if text_data_json['from'] == self.turn_player:
            await self.channel_layer.group_send(
                self.room_group_name,
                text_data_json
            )

    async def turn(self, event):
        me = event['from']
        another_player = 'player1' if me == 'player2' else 'player2'

        turn = me if self.turn_player == another_player else another_player
        self.turn_player = turn
        self.redis.set('{0}_turn'.format(self.room_group_name), self.turn_player)

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
            'turn': self.turn_player,
        }))
