from datetime import timedelta
from collections import defaultdict
from django.utils import timezone
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Visit, VisitorCount

NUM_HITS_SHOWN = 100

@staff_member_required
def index(request):
    update_tables()
    context = { 
        'visitors_per_day': visitors_per_day(),
        'latest_hits': latest_hits(),
    }
    return render(request, 'accesslogger/stats.html', context)

def visitors_per_day():
    MAX_DAYS = 1000
    return VisitorCount.objects.all()[:MAX_DAYS]

def latest_hits():
    return Visit.objects.all()[:NUM_HITS_SHOWN]

def update_tables():
    visitors_per_day = {} # day -> set of IP addresses
    counter = 0
    delete = False
    for visit in Visit.objects.all():
        day = visit.date.date()
        if not day in visitors_per_day.keys():
            visitors_per_day[day] = set()
            if counter > NUM_HITS_SHOWN:
                delete = True
        visitors_per_day[day].add(visit.ip)
        if delete:
            visit.delete()
        counter += 1
    for day, ips in visitors_per_day.items():
        try:
            daycount = VisitorCount.objects.get(day=day)
        except Exception:
            daycount = VisitorCount(day=day)
        daycount.count = len(ips)
        daycount.save()
