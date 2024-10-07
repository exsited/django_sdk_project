from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ab_py.common.ab_exception import ABException
from ab_py.exsited.exsited_sdk import ExsitedSDK
from tests.common.common_data import CommonData
from .utils import fetch_call_usage, fetch_message_usage


@api_view(['POST'])
def call_usage(request):
    call_usage_data = fetch_call_usage()
    return JsonResponse({"status": "success", "usage:": call_usage_data}, safe=False)


@api_view(['POST'])
def message_usage(request):
    message_usage_data = fetch_message_usage()
    return JsonResponse({"status": "success", "usage:": message_usage_data}, safe=False)


