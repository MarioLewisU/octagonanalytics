from django.shortcuts import render
from django.http import JsonResponse
from fighters.models import Fighter
from fights.models import FightStat
from django.db.models import Q

def search_fighter(request):
    query = request.GET.get('q', '').strip()
    fighters = []

    if query:
        parts = query.split()
        if len(parts) == 1:
            fighters = Fighter.objects.filter(first_name__icontains=parts[0]) | Fighter.objects.filter(last_name__icontains=parts[0])
        elif len(parts) >= 2:
            fighters = Fighter.objects.filter(first_name__icontains=parts[0], last_name__icontains=parts[1])

    # Attach stats to each fighter
    for fighter in fighters:
        stats_qs = FightStat.objects.filter(fighter=fighter)
        if stats_qs.exists():
            fighter.fight_stats = {
            "total_kd": sum(s.knockdowns for s in stats_qs),
            "total_sig": sum(s.sig_strikes for s in stats_qs),
            "total_sig_att": sum(s.sig_strikes_attempted for s in stats_qs),
            "total_td": sum(s.takedowns for s in stats_qs),
            "total_td_att": sum(s.takedowns_attempted for s in stats_qs),
            "total_ctrl": sum(s.control_time for s in stats_qs),
            "submission_attempts": sum(s.submission_attempts for s in stats_qs),
            "reversals": sum(s.reversals for s in stats_qs),
            "head_strikes": sum(s.head_strikes for s in stats_qs),
            "head_strikes_attempted": sum(s.head_strikes_attempted for s in stats_qs),
            "body_strikes": sum(s.body_strikes for s in stats_qs),
            "body_strikes_attempted": sum(s.body_strikes_attempted for s in stats_qs),
            "leg_strikes": sum(s.leg_strikes for s in stats_qs),
            "leg_strikes_attempted": sum(s.leg_strikes_attemped for s in stats_qs),
            "distance_strikes": sum(s.distance_strikes for s in stats_qs),
            "distance_strikes_attempted": sum(s.distance_strikes_attempted for s in stats_qs),
            "clinch_strikes": sum(s.clinch_strikes for s in stats_qs),
            "clinch_strikes_attempted": sum(s.clinch_strikes_attempted for s in stats_qs),
            "ground_strikes": sum(s.ground_strikes for s in stats_qs),
            "ground_strikes_attempted": sum(s.ground_strikes_attemped for s in stats_qs),
        }
        else:
            fighter.fight_stats = None


    context = {
        "fighters": fighters,
        "query": query,
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
