import channels.layers
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

    # TODO game state - if doesn't exist, store it (redis)
    channel_layer = channels.layers.get_channel_layer()
    channel_layer.send('game_channel_{0}'.format(room_name), {
        'type': 'check_game_state',
        'character': request.COOKIES['char_choice'],
    })

    return render(request, 'play.html', {})
