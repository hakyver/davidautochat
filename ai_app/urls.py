from django.urls import path
from . import views

urlpatterns = [
    path('send-message/', views.send_message, name='send_message'),
    path('flow-schedule/', views.flow_schedule, name='flow_schedule'),
    path('flow-seller/', views.flow_seller, name='flow_seller'),
    path('welcome-flow/', views.welcome_flow, name='welcome_flow'),
    path('flow-confirm/', views.flow_confirm, name='flow_confirm'),
    path('handle-intent/', views.handle_intent, name='handle_intent'),
]


    