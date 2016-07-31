from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Visit

@staff_member_required
def index(request):
    context = { 
        'hits_per_day': hits_per_day(),
        'latest_hits': latest_hits(),
    }
    return render(request, 'accesslogger/stats.html', context)

def hits_per_day():
    NUM_DAYS = 30
    res = {}
    day = datetime.today()
    for i in range(NUM_DAYS):
        res[day] = Visit.objects.filter(date__date=day).count()
        day -= timedelta(days=1)
    return sorted(res.items())

def latest_hits():
    NUM_HITS = 100
    return Visit.objects.all()[:NUM_HITS]
