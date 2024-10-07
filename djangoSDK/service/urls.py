from django.urls import path

from . import views

urlpatterns = [
    path("create/usage/call/", views.call_usage, name="call_usage"),
    path("create/usage/message/", views.message_usage, name="message_usage"),
]