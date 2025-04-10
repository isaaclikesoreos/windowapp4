from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView, DetailView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import datetime, timedelta
from windshields.models import JobEntry, Quote, Appointment, InsuranceClaim, TimeSlot
from .models import AdminPreference

def is_admin_user(user):
    """Check if the user is an admin or staff member"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin that requires the user to be an admin/staff"""
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def handle_no_permission(self):
        return redirect('home')

class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Main dashboard view for the administrative console"""
    template_name = 'a_administration/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Get recent job entries
        context['recent_job_entries'] = JobEntry.objects.all().order_by('-created_at')[:5]
        
        # Get today's appointments
        context['todays_appointments'] = Appointment.objects.filter(
            appointment_date__date=today
        ).order_by('appointment_date')[:5]
        context['todays_appointments_count'] = Appointment.objects.filter(
            appointment_date__date=today
        ).count()
        
        # Get pending quotes (without appointments)
        pending_quotes = Quote.objects.filter(
            insurance_claims__isnull=True  # No insurance claim
        ).order_by('-created_at')
        context['pending_quotes'] = pending_quotes[:5]
        context['pending_quotes_count'] = pending_quotes.count()
        
        # Get pending insurance claims
        pending_claims = InsuranceClaim.objects.filter(
            status='initiated'
        ).order_by('-loss_date')
        context['pending_claims'] = pending_claims[:5]
        context['pending_claims_count'] = pending_claims.count()
        
        # Get jobs for current month
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1)) \
            if first_day_of_month.month < 12 else first_day_of_month.replace(year=first_day_of_month.year + 1, month=1, day=1) - timedelta(days=1)
        
        context['month_jobs_count'] = JobEntry.objects.filter(
            created_at__date__gte=first_day_of_month,
            created_at__date__lte=last_day_of_month
        ).count()
        
        # Get admin preferences
        try:
            if self.request.user.admin_preferences:
                context['admin_prefs'] = self.request.user.admin_preferences
        except:
            # Default preferences if none exist
            context['admin_prefs'] = None
        
        return context

class JobEntryDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View for viewing the full details of a job entry"""
    model = JobEntry
    template_name = 'a_administration/job_entry_detail.html'
    context_object_name = 'job_entry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_entry = self.get_object()
        
        # Get related quote
        context['quote'] = job_entry.quotes.first()
        
        # Get related claim if exists
        if context['quote']:
            context['claim'] = context['quote'].insurance_claims.first()
        
        # Get related appointment if exists
        if context['claim']:
            context['appointment'] = context['claim'].appointments.first()
        
        return context

class AppointmentDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View for viewing the full details of an appointment"""
    model = Appointment
    template_name = 'a_administration/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.get_object()
        
        # Get related claim if exists
        context['claim'] = appointment.claim
        
        # Get related quote if exists
        if context['claim']:
            context['quote'] = context['claim'].quote
            
            # Get related job entry
            if context['quote']:
                context['job_entry'] = context['quote'].job_entry
        
        return context
    


# Add this to your views.py file

class TimeSlotManagementView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """View for managing time slots"""
    template_name = 'a_administration/timeslot_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range for filtering
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Default to current week
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = start_date + timedelta(days=6)  # Sunday
        
        # Get time slots for the selected date range
        time_slots = TimeSlot.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'start_time')
        
        # Group time slots by date
        slots_by_date = {}
        for slot in time_slots:
            date_str = slot.date.strftime('%Y-%m-%d')
            if date_str not in slots_by_date:
                slots_by_date[date_str] = []
            slots_by_date[date_str].append(slot)
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['slots_by_date'] = slots_by_date
        
        return context
    



# Add this to your views.py file

class QuoteListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View for listing all quotes"""
    model = Quote
    template_name = 'a_administration/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Quote.objects.all().order_by('-created_at')
        
        # Filter by quote type if specified
        quote_type = self.request.GET.get('type')
        if quote_type in ('repair', 'replacement'):
            queryset = queryset.filter(quote_type=quote_type)
        
        # Filter by status if specified
        status = self.request.GET.get('status')
        if status == 'pending':
            # Quotes with no appointments
            queryset = queryset.filter(insurance_claims__isnull=True)
        elif status == 'approved':
            # Quotes with approved insurance claims
            queryset = queryset.filter(insurance_claims__status='approved')
        elif status == 'scheduled':
            # Quotes with scheduled appointments
            queryset = queryset.filter(insurance_claims__status='scheduled')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quote_type'] = self.request.GET.get('type', '')
        context['status'] = self.request.GET.get('status', '')
        return context


class QuoteDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View for viewing the full details of a quote"""
    model = Quote
    template_name = 'a_administration/quote_detail.html'
    context_object_name = 'quote'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote = self.get_object()
        
        # Get related job entry
        context['job_entry'] = quote.job_entry
        
        # Get related claim if exists
        context['claim'] = quote.insurance_claims.first() if quote.insurance_claims.exists() else None
        
        # Get related appointment if exists
        if context['claim']:
            context['appointment'] = context['claim'].appointments.first() if context['claim'].appointments.exists() else None
        
        return context