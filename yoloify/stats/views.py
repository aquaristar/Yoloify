import json
from django.http import HttpResponse
from yoloify.stats.models import UsageStatsDaily
from yoloify.utils.views import JSONEncoder


def usage_stats_daily(request):
    start = request.GET.get('from_date', None)
    end = request.GET.get('to_date', None)

    response_data = UsageStatsDaily.usage_stats_daily(start, end)
    response_data = json.dumps(response_data, cls=JSONEncoder)

    return HttpResponse(response_data, content_type="application/json")


def usage_stats_total(request):
    start = request.GET.get('from_date', None)
    end = request.GET.get('to_date', None)

    response_data = UsageStatsDaily.usage_stats_total(start, end)
    response_data = json.dumps(response_data, cls=JSONEncoder)

    return HttpResponse(response_data, content_type="application/json")


#temp
def usage_start_task(request):
    from yoloify.stats.tasks import aggregate_usage_stats

    aggregate_usage_stats.apply_async()

    return HttpResponse('celery task, only one time excution')
