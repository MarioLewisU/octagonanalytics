from django.shortcuts import render
from django.http import JsonResponse
from fighters.models import Fighter
from django.db.models import Q

def search_fighter(request):
    query = request.GET.get('q', '').strip()
    fighters = []

    if query:
        # Split query into words
        parts = query.split()
        if len(parts) == 1:
            # Search by first OR last name
            fighters = Fighter.objects.filter(first_name__icontains=parts[0]) | Fighter.objects.filter(last_name__icontains=parts[0])
        elif len(parts) >= 2:
            # Search by first AND last name
            fighters = Fighter.objects.filter(first_name__icontains=parts[0], last_name__icontains=parts[1])

    context = {
        'fighters': fighters,
        'query': query
    }
    return render(request, 'fighters/search_fighter.html', context)

def fighter_results(request):
    query = request.GET.get("q", "")
    fighters = Fighter.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(first_name__icontains=query.split(" ")[0], last_name__icontains=" ".join(query.split(" ")[1:]))
    )
    
    return render(request, "fighters/fighter_results.html", {"fighters": fighters, "query": query})

def autocomplete_fighters(request):
    query = request.GET.get('q', '')
    fighters = Fighter.objects.filter(first_name__istartswith=query) | Fighter.objects.filter(last_name__istartswith=query)
    names = [f"{f.first_name} {f.last_name}" for f in fighters]
    return JsonResponse(names, safe=False)