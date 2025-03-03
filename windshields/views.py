import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic.edit import FormView
from .forms import JobEntryForm
from .models import *
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date


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
                # Adjust this as needed to match your actual relationship.
                try:
                    customer_instance = Customer.objects.get(user=request.user)
                except Customer.DoesNotExist:
                    logger.error("No Customer instance found for user: %s", request.user)
                    return JsonResponse({
                        'success': False,
                        'errors': {'customer': 'No customer profile found for this user.'}
                    }, status=400)
                
                # If the job entry qualifies for a windshield repair quote...
                if job_entry.damage_piece == 'windshield' and job_entry.is_repairable:
                    quote = Quote.objects.create(
                        job_entry=job_entry,
                        quote_type='repair',
                        installation_labor=69,
                        customer=request.user,  # Quote uses User (AUTH_USER_MODEL)
                        vehicle=getattr(request.user, 'vehicle', None),
                    )
                    logger.debug("Quote created with ID: %s", quote.id)
                    
                    # If the job_entry includes insurance information, create an InsuranceClaim.
                    if job_entry.has_insurance_claim:
                        claim = InsuranceClaim.objects.create(
                            customer=customer_instance,  # Not request.user!
                            insurance_name=job_entry.insurance_name,
                            insurance_id="",  # update as needed
                            referral_number=job_entry.referral_number,
                            dispatch_number="",  # update as needed
                            deductible=0,
                            status="initiated",
                            loss_date=timezone.now().date(),
                            damage_area=job_entry.damage_piece,
                            damage_side=job_entry.damage_side,
                            quote=quote,
                        )

                        logger.debug("InsuranceClaim created with ID: %s", claim.id)
                    
                    redirect_url = '/windshields/repair-quote/?job_entry_id=' + str(job_entry.id)
                
                # Additional logic for other quote types would go here.
                
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
        job_entry = get_object_or_404(JobEntry, id=job_entry_id)
        context['job_entry'] = job_entry
        
        # Get the quote created for this job entry, if any.
        quote = job_entry.quotes.first()  # Assumes one quote per job entry
        context['quote'] = quote
        
        if job_entry.has_insurance_claim:
            context['message'] = "Rock chip repairs are usually instantly approved by your insurance, please make sure your claim is assigned to our shop."
        else:
            context['message'] = "Your windshield repair quote is $69"
        
        return context





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