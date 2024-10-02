from django.urls import path

from . import views

urlpatterns = [
    path("usage/call/", views.call_usage, name="call_usage"),
    path("usage/message/", views.message_usage, name="message_usage"),
]