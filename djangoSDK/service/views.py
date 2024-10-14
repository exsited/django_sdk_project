from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from .utils import fetch_call_usage, fetch_message_usage


def respond_with_usage(fetch_function):
    try:
        usage_data = fetch_function()
        return JsonResponse({"status": "complete", "usage": usage_data}, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@api_view(['POST'])
def call_usage(request):
    return respond_with_usage(fetch_call_usage)


@api_view(['POST'])
def message_usage(request):
    return respond_with_usage(fetch_message_usage)
