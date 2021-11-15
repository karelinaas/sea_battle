import json

from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(GameConsumer, self).__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.channel_name = None

    async def connect(self):
        # TODO if receive_count > 2, close
        if self.channel_layer.receive_count > 2:
            await self.close()

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_{0}'.format(self.room_name)
        self.channel_name = 'game_channel_{0}'.format(self.room_name)

        await self.accept()

