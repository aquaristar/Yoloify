from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from yoloify.stats.models import UsageStatsDaily


@staff_member_required
def index(request):
    usage = UsageStatsDaily.usage_stats_total()
    return render(request, 'cpanel/index.html', {'usage': usage})
