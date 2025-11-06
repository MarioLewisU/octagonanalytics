from django.shortcuts import render
from events.models import Event


def past_events(request):
    past_events = Event.objects.order_by('-date')[:5]
    
    context = {
        'past_events': past_events
    }

    return render(request, 'events/past_events.html', context)
