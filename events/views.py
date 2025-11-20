from django.shortcuts import render
from events.models import Event
import json
import os
from django.conf import settings

def home_events(request):
    # past 10 events
    past_events = Event.objects.order_by('-date')[:10]
    
    # upcoming events for json
    event_name = None
    event_date = None
    event_location = None
    fights = []
    
    json_file_path = os.path.join(settings.BASE_DIR, 'next_event.json')
    
    try:
        with open(json_file_path, 'r') as f:
            event_data = json.load(f)
        
        event_name = event_data.get('name', 'No event found')
        event_date = event_data.get('date', 'TBD')
        event_location = event_data.get('location', 'TBD')
        fights = event_data.get('fights', [])
        
        print(f"Loaded upcoming event: {event_name}")
        print(f"Number of fights: {len(fights)}")
        
    except FileNotFoundError:
        print("next_event.json file not found")
    except Exception as e:
        print(f"Error loading JSON: {e}")
    
    context = {
        'event_name': event_name,
        'event_date': event_date,
        'event_location': event_location,
        'fights': fights,
        'past_events': past_events
    }

    return render(request, 'events/home.html', context)