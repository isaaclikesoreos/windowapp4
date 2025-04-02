import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic.edit import FormView
from .forms import JobEntryForm
from .models import *
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import AppointmentSerializer

logger = logging.getLogger(__name__)

class QuoteStartView(FormView):
    template_name = 'windshields/quote_start.html'
    form_class = JobEntryForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            logger.debug("Received POST data: %s", request.POST)
            if form.is_valid():
                job_entry = form.save()
                logger.debug("JobEntry saved with ID: %s", job_entry.id)
                
                quote = None
                claim = None
                redirect_url = ''

                # Get the customer instance associated with this user.
                try:
                    customer_instance = Customer.objects.get(user=request.user)
                except Customer.DoesNotExist:
                    logger.error("No Customer instance found for user: %s", request.user)
                    return JsonResponse({
                        'success': False,
                        'errors': {'customer': 'No customer profile found for this user.'}
                    }, status=400)
                
                # CASE 1: Windshield repair quote
                if job_entry.damage_piece == 'windshield' and job_entry.is_repairable:
                    quote = Quote.objects.create(
                        job_entry=job_entry,
                        quote_type='repair',
                        installation_labor=69,
                        customer=request.user,
                        vehicle=getattr(request.user, 'vehicle', None),
                    )
                    logger.debug("Repair Quote created with ID: %s", quote.id)
                    
                    # If the job_entry includes insurance information, create an InsuranceClaim
                    if job_entry.has_insurance_claim:
                        claim = InsuranceClaim.objects.create(
                            customer=customer_instance,
                            insurance_name=job_entry.insurance_name,
                            insurance_id=job_entry.policy_number or "",
                            referral_number=job_entry.referral_number or "",
                            dispatch_number=job_entry.claim_number or "",
                            deductible=0,  # Typically $0 for windshield repairs
                            status="initiated",
                            loss_date=timezone.now().date(),
                            damage_area=job_entry.damage_piece,
                            damage_side=job_entry.damage_side,
                            quote=quote,
                        )
                        logger.debug("InsuranceClaim created with ID: %s", claim.id)
                        redirect_url = '/windshields/insurance-repair-quote/?job_entry_id=' + str(job_entry.id)
                    else:
                        # Regular customer pay quote
                        redirect_url = '/windshields/repair-quote/?job_entry_id=' + str(job_entry.id)
                
                # CASE 2: Replacement quote (non-repairable windshield or any other glass)
                else:
                    quote = Quote.objects.create(
                        job_entry=job_entry,
                        quote_type='replacement',
                        installation_labor=0,  # Will be determined later
                        customer=request.user,
                        vehicle=getattr(request.user, 'vehicle', None),
                    )
                    logger.debug("Replacement Quote created with ID: %s", quote.id)
                    
                    # If the job_entry includes insurance information, create an InsuranceClaim
                    if job_entry.has_insurance_claim:
                        claim = InsuranceClaim.objects.create(
                            customer=customer_instance,
                            insurance_name=job_entry.insurance_name,
                            insurance_id=job_entry.policy_number or "",
                            referral_number=job_entry.referral_number or "",
                            dispatch_number=job_entry.claim_number or "",
                            deductible=0,  # Will be determined later
                            status="initiated",
                            loss_date=timezone.now().date(),
                            damage_area=job_entry.damage_piece,
                            damage_side=job_entry.damage_side,
                            quote=quote,
                        )
                        logger.debug("InsuranceClaim created with ID: %s", claim.id)
                        redirect_url = '/windshields/insurance-replacement-quote/?job_entry_id=' + str(job_entry.id)
                    else:
                        # Regular customer pay quote
                        redirect_url = '/windshields/replacement-quote/?job_entry_id=' + str(job_entry.id)
                
                return JsonResponse({
                    'success': True,
                    'job_entry_id': job_entry.id,
                    'redirect_url': redirect_url,
                })
            else:
                logger.debug("Form errors: %s", form.errors)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        else:
            return super().post(request, *args, **kwargs)


class RepairQuoteView(TemplateView):
    template_name = 'windshields/repair_quote.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_entry_id = self.request.GET.get('job_entry_id')
        quote_type = self.request.GET.get('type', 'default')  # Get quote type parameter
        
        job_entry = get_object_or_404(JobEntry, id=job_entry_id)
        context['job_entry'] = job_entry
        
        # Get the quote created for this job entry, if any.
        quote = job_entry.quotes.first()  # Assumes one quote per job entry
        context['quote'] = quote
        
        # Handle explicit customer pay request
        if quote_type == 'customer':
            context['is_insurance'] = False
            context['message'] = "Your windshield repair quote is $69"
        # Default case based on job_entry status
        elif job_entry.has_insurance_claim:
            context['is_insurance'] = True
            context['message'] = "Rock chip repairs are usually instantly approved by your insurance, please make sure your claim is assigned to our shop."
        else:
            context['is_insurance'] = False
            context['message'] = "Your windshield repair quote is $69"
        
        # Send notification if quote exists and notifications haven't been sent yet
        if quote and not quote.pin_sent and not self.request.GET.get('no_notify'):
            from .utils import send_quote_notifications
            notification_result = send_quote_notifications(quote)
            context['notification_sent'] = any(notification_result.values())
        
        return context
    

def get_appointments(request):
    """API endpoint to return all appointments as events for FullCalendar"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    # Default to showing current month if dates not provided
    if not start_date:
        start_date = timezone.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        next_month = timezone.now().replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1).strftime('%Y-%m-%d')
    
    # Filter appointments by date range
    appointments = Appointment.objects.filter(
        appointment_date__gte=start_date,
        appointment_date__lte=end_date
    )
    
    # Format appointments for FullCalendar
    events = []
    for appointment in appointments:
        events.append({
            'id': appointment.id,
            'title': 'Booked',  # Don't show customer name for privacy
            'start': appointment.appointment_date.isoformat(),
            'end': (appointment.appointment_date + timedelta(hours=1)).isoformat(),  # Assuming 1-hour appointments
            'allDay': False,
            'className': 'bg-red-500',  # CSS class for booked slots
        })
    
    return JsonResponse(events, safe=False)


def available_timeslots(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            slots = TimeSlot.objects.filter(date=date_obj, filled=False)
            slots_data = [{
                'id': slot.id,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M')
            } for slot in slots]
            return JsonResponse({'success': True, 'timeslots': slots_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'No date provided'})


@csrf_exempt  # For testing; in production, handle CSRF properly
def schedule_appointment(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        timeslot_ids = request.POST.getlist('timeslot_ids[]')
        service_location = request.POST.get('service_location', 'Default Location')
        if not date_str or not timeslot_ids:
            return JsonResponse({'success': False, 'error': 'Missing date or timeslot information'})
        date_obj = parse_date(date_str)
        # For simplicity, set appointment_date as the date with the earliest start time among the selected slots
        timeslots = TimeSlot.objects.filter(id__in=timeslot_ids)
        if not timeslots.exists():
            return JsonResponse({'success': False, 'error': 'No valid timeslots selected'})
        earliest_slot = timeslots.order_by('start_time').first()
        appointment_datetime = timezone.make_aware(datetime.combine(date_obj, earliest_slot.start_time))
        appointment = Appointment.objects.create(
            customer=request.user,
            vehicle=getattr(request.user, 'vehicle', None),
            service_location=service_location,
            appointment_date=appointment_datetime,
            # If you need to link to a claim, add that here.
        )
        for slot in timeslots:
            appointment.timeslots.add(slot)
            slot.filled = True
            slot.save()
        appointment.save()
        return JsonResponse({'success': True, 'appointment_id': appointment.id})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CalendarView(TemplateView):
    template_name = 'windshields/calendar.html'




class InsuranceRepairQuoteView(TemplateView):
    template_name = 'windshields/repair_quote.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_entry_id = self.request.GET.get('job_entry_id')
        job_entry = get_object_or_404(JobEntry, id=job_entry_id)
        context['job_entry'] = job_entry
        
        # Get the quote created for this job entry, if any.
        quote = job_entry.quotes.first()  # Assumes one quote per job entry
        context['quote'] = quote
        
        # Get the insurance claim associated with this quote, if any
        if quote:
            claim = quote.insurance_claims.first()
            context['claim'] = claim
        
        # Set the template to display insurance-specific information
        context['is_insurance'] = True
        context['message'] = "Insurance fully approves windshield repairs"
        
        # Send notification if quote exists and notifications haven't been sent yet
        if quote and not quote.pin_sent and not self.request.GET.get('no_notify'):
            from .utils import send_quote_notifications
            notification_result = send_quote_notifications(quote)
            context['notification_sent'] = any(notification_result.values())
        
        return context
    


@csrf_exempt  # For testing; in production, handle CSRF properly
def schedule_appointment(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        timeslot_ids = request.POST.getlist('timeslot_ids[]')
        service_location = request.POST.get('service_location', 'Default Location')
        claim_id = request.POST.get('claim_id')  # Allow passing a claim ID
        
        if not date_str or not timeslot_ids:
            return JsonResponse({'success': False, 'error': 'Missing date or timeslot information'})
        
        date_obj = parse_date(date_str)
        # For simplicity, set appointment_date as the date with the earliest start time among the selected slots
        timeslots = TimeSlot.objects.filter(id__in=timeslot_ids)
        if not timeslots.exists():
            return JsonResponse({'success': False, 'error': 'No valid timeslots selected'})
        
        earliest_slot = timeslots.order_by('start_time').first()
        appointment_datetime = timezone.make_aware(datetime.combine(date_obj, earliest_slot.start_time))
        
        # Get associated claim if claim_id is provided
        claim = None
        if claim_id:
            try:
                claim = InsuranceClaim.objects.get(id=claim_id)
            except InsuranceClaim.DoesNotExist:
                logger.warning(f"Claim ID {claim_id} does not exist")
        
        # Create the appointment
        appointment = Appointment.objects.create(
            customer=request.user,
            vehicle=getattr(request.user, 'vehicle', None),
            service_location=service_location,
            appointment_date=appointment_datetime,
            claim=claim
        )
        
        # Mark timeslots as filled
        for slot in timeslots:
            appointment.timeslots.add(slot)
            slot.filled = True
            slot.save()
        
        appointment.save()
        
        # If this is an insurance claim appointment, update the claim status
        if claim:
            claim.status = "scheduled"
            claim.save()
            logger.info(f"Updated claim {claim.id} status to 'scheduled'")
        
        return JsonResponse({
            'success': True, 
            'appointment_id': appointment.id,
            'has_claim': claim is not None
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



@csrf_exempt  # For testing; in production, handle CSRF properly
def update_insurance_info(request):
    """View to handle updating insurance information for a job entry"""
    if request.method == 'POST':
        job_entry_id = request.POST.get('job_entry_id')
        insurance_name = request.POST.get('insurance_name', '')
        policy_number = request.POST.get('policy_number', '')
        claim_number = request.POST.get('claim_number', '')
        referral_number = request.POST.get('referral_number', '')
        
        if not job_entry_id:
            return JsonResponse({'success': False, 'error': 'Missing job entry ID'})
        
        try:
            job_entry = JobEntry.objects.get(id=job_entry_id)
            
            # Check if insurance status is changing
            was_insurance = job_entry.has_insurance_claim
            has_insurance_now = bool(insurance_name or policy_number or claim_number)
            status_changed = was_insurance != has_insurance_now
            
            # Update the job entry with the new insurance information
            job_entry.insurance_name = insurance_name
            job_entry.policy_number = policy_number
            job_entry.claim_number = claim_number
            job_entry.referral_number = referral_number
            job_entry.has_insurance_claim = has_insurance_now
            job_entry.save()
            
            # Check if there's an existing quote for this job entry
            quote = job_entry.quotes.first()
            if quote:
                claim = None
                if quote.insurance_claims.exists():
                    claim = quote.insurance_claims.first()
                    
                    if has_insurance_now:
                        # Update the claim with new insurance information
                        claim.insurance_name = insurance_name
                        claim.insurance_id = policy_number
                        claim.dispatch_number = claim_number
                        claim.referral_number = referral_number
                        claim.save()
                    else:
                        # If no insurance info now, delete the claim
                        claim.delete()
                        claim = None
                        
                elif has_insurance_now:
                    # Create a new claim if there isn't one but the job entry has insurance
                    try:
                        customer_instance = Customer.objects.get(user=request.user)
                        claim = InsuranceClaim.objects.create(
                            customer=customer_instance,
                            insurance_name=insurance_name,
                            insurance_id=policy_number,
                            dispatch_number=claim_number,
                            referral_number=referral_number,
                            deductible=0,  # Will be determined later based on quote type
                            status="initiated",
                            loss_date=timezone.now().date(),
                            damage_area=job_entry.damage_piece,
                            damage_side=job_entry.damage_side,
                            quote=quote,
                        )
                    except Customer.DoesNotExist:
                        logger.error(f"No customer instance found for user {request.user}")
                        return JsonResponse({
                            'success': False,
                            'error': 'No customer profile found for this user.'
                        })
            
            return JsonResponse({
                'success': True,
                'job_entry_id': job_entry.id,
                'has_insurance_claim': job_entry.has_insurance_claim,
                'reload': status_changed  # Tell the frontend to reload if insurance status changed
            })
            
        except JobEntry.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Job entry not found'})
        except Exception as e:
            logger.error(f"Error updating insurance info: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



class ReplacementQuoteView(TemplateView):
    template_name = 'windshields/replacement_quote.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_entry_id = self.request.GET.get('job_entry_id')
        job_entry = get_object_or_404(JobEntry, id=job_entry_id)
        context['job_entry'] = job_entry
        
        # Get the quote created for this job entry, if any
        quote = job_entry.quotes.first()  # Assumes one quote per job entry
        context['quote'] = quote
        
        # Get the insurance claim associated with this quote, if any
        if quote and quote.insurance_claims.exists():
            claim = quote.insurance_claims.first()
            context['claim'] = claim
            context['is_insurance'] = True
        else:
            context['is_insurance'] = job_entry.has_insurance_claim
        
        # Set appropriate message based on damage type and insurance status
        if job_entry.damage_piece == 'windshield':
            if job_entry.has_insurance_claim:
                context['message'] = f"Insurance claim for {job_entry.get_damage_piece_display()} replacement"
            else:
                context['message'] = f"Your {job_entry.get_damage_piece_display()} replacement quote"
        else:
            # For non-windshield glass replacements
            damage_text = job_entry.get_damage_piece_display()
            if job_entry.damage_side:
                damage_text = f"{job_entry.get_damage_side_display()} {damage_text}"
                
            if job_entry.has_insurance_claim:
                context['message'] = f"Insurance claim for {damage_text} replacement"
            else:
                context['message'] = f"Your {damage_text} replacement quote"
        
        # For now, we'll hide the scheduling section
        context['show_scheduling'] = False
        
        # Send notification if quote exists and notifications haven't been sent yet
        if quote and not quote.pin_sent and not self.request.GET.get('no_notify'):
            from .utils import send_quote_notifications
            notification_result = send_quote_notifications(quote)
            context['notification_sent'] = any(notification_result.values())
        
        return context
    



class InsuranceReplacementQuoteView(TemplateView):
    template_name = 'windshields/replacement_quote.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_entry_id = self.request.GET.get('job_entry_id')
        job_entry = get_object_or_404(JobEntry, id=job_entry_id)
        context['job_entry'] = job_entry
        
        # Get the quote created for this job entry, if any
        quote = job_entry.quotes.first()  # Assumes one quote per job entry
        context['quote'] = quote
        
        # Get the insurance claim associated with this quote, if any
        if quote:
            claim = quote.insurance_claims.first()
            context['claim'] = claim
        
        # Set context for insurance case
        context['is_insurance'] = True
        
        # Set appropriate message based on damage type
        if job_entry.damage_piece == 'windshield':
            context['message'] = "Insurance claim for windshield replacement"
        else:
            # For non-windshield glass replacements
            damage_text = job_entry.get_damage_piece_display()
            if job_entry.damage_side:
                damage_text = f"{job_entry.get_damage_side_display()} {damage_text}"
            context['message'] = f"Insurance claim for {damage_text} replacement"
        
        # For now, we'll hide the scheduling section
        context['show_scheduling'] = False
        
        # Send notification if quote exists and notifications haven't been sent yet
        if quote and not quote.pin_sent and not self.request.GET.get('no_notify'):
            from .utils import send_quote_notifications
            notification_result = send_quote_notifications(quote)
            context['notification_sent'] = any(notification_result.values())
        
        return context
    



@csrf_exempt
def request_callback(request):
    """Handle callback requests for replacement quotes"""
    if request.method == 'POST':
        job_entry_id = request.POST.get('job_entry_id')
        preferred_time = request.POST.get('preferred_time', '')
        additional_notes = request.POST.get('additional_notes', '')
        
        if not job_entry_id:
            return JsonResponse({'success': False, 'error': 'Missing job entry ID'})
        
        try:
            job_entry = JobEntry.objects.get(id=job_entry_id)
            quote = job_entry.quotes.first()
            
            if not quote:
                return JsonResponse({'success': False, 'error': 'No quote found for this job entry'})
            
            # In a real application, you would create a callback request record
            # and potentially trigger notifications to staff
            # For now, just log the request
            
            logger.info(
                f"Callback requested for job entry {job_entry_id} by {request.user.username}. "
                f"Name: {job_entry.first_name} {job_entry.last_name}, "
                f"Phone: {job_entry.phone}, "
                f"Preferred time: {preferred_time}, "
                f"Notes: {additional_notes}"
            )
            
            # If we had a CallbackRequest model, we would save it here
            # For example:
            # CallbackRequest.objects.create(
            #     job_entry=job_entry,
            #     quote=quote,
            #     customer=request.user,
            #     preferred_time=preferred_time,
            #     additional_notes=additional_notes,
            #     status='pending'
            # )
            
            return JsonResponse({
                'success': True,
                'message': 'Callback request received. Our team will contact you shortly.'
            })
            
        except JobEntry.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Job entry not found'})
        except Exception as e:
            logger.error(f"Error requesting callback: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)