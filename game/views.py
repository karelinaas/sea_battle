from django.shortcuts import render, redirect


def index(request):
    if request.method == 'POST':
        room_code = request.POST.get('room_code')
        char_choice = request.POST.get('character_choice')
        return redirect('/play/{0}?choice={1}'.format(room_code, char_choice))
    return render(request, 'index.html', {})
