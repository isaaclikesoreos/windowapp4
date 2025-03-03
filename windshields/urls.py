from django.urls import path
from .views import QuoteStartView, RepairQuoteView, available_timeslots, schedule_appointment

urlpatterns = [
    path('quote_start/', QuoteStartView.as_view(), name='quote_start'),
    path('repair-quote/', RepairQuoteView.as_view(), name='repair_quote'),
    path('available-timeslots/', available_timeslots, name='available_timeslots'),
    path('schedule-appointment/', schedule_appointment, name='schedule_appointment'),
]
