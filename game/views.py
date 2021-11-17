import json

import redis
from django.shortcuts import render, redirect
from django.urls import reverse


def index(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        char_choice = request.POST.get('character_choice')

        response = redirect(reverse('play', kwargs={'room_name': room_name}))
        response.set_cookie('char_choice', char_choice, 3600)

        return response
    return render(request, 'index.html', {})


def play(request, room_name):
    if 'char_choice' not in request.COOKIES or request.COOKIES['char_choice'] not in ('player1', 'player2'):
        return redirect(reverse('index'))

    player = request.COOKIES['char_choice']

    r = redis.Redis(host='redis', port=6379, db=0)

    # current player's field
    # TODO format
    field_json = r.get('field_' + room_name + '_' + player)
    # another player's field
    another_field_json = r.get('another_field_' + room_name + '_' + player)

    var_dict = {
        'field': field_json,
        'another_field': another_field_json,
        'chat_log': [],
    }

    # TODO вынести в хелпер
    for i, field in var_dict.items():
        if not field:
            if i == 'field':
                if player == 'player1':
                    field = [
                        [0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 1, 1, 1, 0, 0, 1],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 1, 1, 0, 0, 0, 0, 0, 1, 1],
                        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
                    ]
                else:
                    field = [
                        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                        [1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                        [1, 0, 1, 1, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    ]
            else:
                field = [[0 for col in range(10)] for row in range(10)]

            # TODO format
            r.set(i + '_' + room_name + '_' + player, json.dumps(field))
        else:
            field = json.loads(field)
        var_dict[i] = enumerate(field)

    var_dict['room_name'] = room_name
    var_dict['player'] = player
    var_dict['num'] = player.replace('player', '')

    turn_player = r.get('game_{0}_turn'.format(room_name))
    var_dict['turn_player'] = turn_player.decode('ascii').replace('player', '') if turn_player else 'player1'

    keys = r.keys(pattern='chat_{0}_*'.format(room_name))
    chat_log = r.mget(keys)
    if chat_log:
        var_dict['chat_log'] = [json.loads(message) for message in chat_log]
        var_dict['chat_log'] = sorted(var_dict['chat_log'], key=lambda x: (x['time_unix']))
    print(var_dict['chat_log'])

    return render(request, 'play.html', var_dict)
