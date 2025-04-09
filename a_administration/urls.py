from django.urls import path
from . import views
from . import utils

app_name = 'a_administration'

urlpatterns = [
    # Main views
    path('console/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('job-entries/<int:pk>/', views.JobEntryDetailView.as_view(), name='job_entry_detail'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('timeslots/', views.TimeSlotManagementView.as_view(), name='timeslot_management'),
    
    # API utility endpoints
    path('api/resend-notification/<int:quote_id>/', utils.resend_notification, name='resend_notification'),
    path('api/generate-timeslots/', utils.generate_timeslots, name='generate_timeslots'),
    path('api/delete-timeslot/<int:timeslot_id>/', utils.delete_timeslot, name='delete_timeslot'),
    path('api/confirm-appointment/<int:appointment_id>/', utils.confirm_appointment, name='confirm_appointment'),
    path('api/cancel-appointment/<int:appointment_id>/', utils.cancel_appointment, name='cancel_appointment'),
    path('api/approve-quote/<int:quote_id>/', utils.approve_quote, name='approve_quote'),
]