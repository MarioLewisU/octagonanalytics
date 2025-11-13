from django.shortcuts import render
from events.models import Event
from fighters.models import Fighter

def events_home(request):
    past_events = Event.objects.order_by('-date')[:5]

    # Hardcoded upcoming event info
    event_name = "UFC 322: Della Maddalena vs Makhachev"
    event_date = "November 15th, 2025"
    event_location = "New York: Madison Square Garden"

    # Define the fighters for each fight
    fighters_data = [
        (("Jack", "Della Maddalena"), ("Islam", "Makhachev")),
        (("Valentina", "Shevchenko"), ("Zhang", "Weili")),
        (("Sean", "Brady"), ("Michael", "Morales")),
        (("Leon", "Edwards"), ("Carlos", "Prates")),
        (("Beneil", "Dariush"), ("Benoit", "Saint Denis")),
    ]

    fights = []
    for f1, f2 in fighters_data:
        try:
            fighter1 = Fighter.objects.get(first_name=f1[0], last_name=f1[1])
            fighter2 = Fighter.objects.get(first_name=f2[0], last_name=f2[1])
            fights.append({"fighter1": fighter1, "fighter2": fighter2})
        except Fighter.DoesNotExist:
            # Skip this fight if a fighter is missing
            continue

    context = {
        "past_events": past_events,
        "event_name": event_name,
        "event_date": event_date,
        "event_location": event_location,
        "fights": fights,
    }

    return render(request, "events/home.html", context)
