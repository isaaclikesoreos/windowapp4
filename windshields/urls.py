
from django.urls import path, include
from . import views
from .views import QuoteStartView
from a_home.views import QuoteLookupFormView

urlpatterns = [
    path('quote_start/', QuoteStartView.as_view(), name='quote_start'),
    # Repair quote paths
    path('repair-quote/', views.RepairQuoteView.as_view(), name='repair_quote'),
    path('insurance-repair-quote/', views.InsuranceRepairQuoteView.as_view(), name='insurance_repair_quote'),
    # Replacement quote paths
    path('replacement-quote/', views.ReplacementQuoteView.as_view(), name='replacement_quote'),
    path('insurance-replacement-quote/', views.InsuranceReplacementQuoteView.as_view(), name='insurance_replacement_quote'),
    # Quote lookup paths
    path('quote-lookup/', QuoteLookupFormView.as_view(), name='quote_lookup_form'),

    # Common paths
    path('available-timeslots/', views.available_timeslots, name='available_timeslots'),
    path('schedule-appointment/', views.schedule_appointment, name='schedule_appointment'),
    path('update-insurance-info/', views.update_insurance_info, name='update_insurance_info'),
    path('request-callback/', views.request_callback, name='request_callback'),
]