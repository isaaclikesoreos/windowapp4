from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from windshields.models import Quote, TimeSlot, Appointment
from windshields.utils import send_quote_notifications
from datetime import datetime, timedelta
import json

def is_admin_user(user):
    """Check if the user is an admin or staff member"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin_user)
def resend_notification(request, quote_id):
    """Resend notification for a quote"""
    quote = get_object_or_404(Quote, id=quote_id)
    
    # Mark pin as not sent to force resending
    quote.pin_sent = False
    quote.save(update_fields=['pin_sent'])
    
    # Send the notifications
    notification_result = send_quote_notifications(quote)
    
    return JsonResponse({
        'success': True,
        'message': 'Quote notification resent successfully',
        'details': notification_result
    })

@login_required
@user_passes_test(is_admin_user)
def generate_timeslots(request):
    """Generate time slots for a date range"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
            start_time = datetime.strptime(data.get('start_time'), '%H:%M').time()
            end_time = datetime.strptime(data.get('end_time'), '%H:%M').time()
            slot_duration = int(data.get('slot_duration', 30))  # in minutes
            weekdays = data.get('weekdays', [0, 1, 2, 3, 4])  # Default: Monday to Friday
            
            slots_created = 0
            current_date = start_date
            
            while current_date <= end_date:
                # Skip days not in weekdays
                if current_date.weekday() not in weekdays:
                    current_date += timedelta(days=1)
                    continue
                
                # Generate slots for the day
                current_datetime = datetime.combine(current_date, start_time)
                end_datetime = datetime.combine(current_date, end_time)
                
                while current_datetime + timedelta(minutes=slot_duration) <= end_datetime:
                    next_datetime = current_datetime + timedelta(minutes=slot_duration)
                    
                    # Create the timeslot if it doesn't already exist
                    _, created = TimeSlot.objects.get_or_create(
                        date=current_date,
                        start_time=current_datetime.time(),
                        end_time=next_datetime.time(),
                        defaults={'filled': False}
                    )
                    
                    if created:
                        slots_created += 1
                    
                    current_datetime = next_datetime
                
                current_date += timedelta(days=1)
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully generated {slots_created} time slots',
                'slots_created': slots_created
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error generating time slots: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
@user_passes_test(is_admin_user)
def confirm_appointment(request, appointment_id):
    """Confirm an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    appointment.is_approved = True
    appointment.save(update_fields=['is_approved'])
    
    # If there's a claim, update its status
    if appointment.claim:
        appointment.claim.status = 'scheduled'
        appointment.claim.save(update_fields=['status'])
    
    return JsonResponse({
        'success': True,
        'message': 'Appointment confirmed successfully'
    })

@login_required
@user_passes_test(is_admin_user)
def cancel_appointment(request, appointment_id):
    """Cancel an appointment and free up its time slots"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Free up the time slots
    time_slots = appointment.timeslots.all()
    for slot in time_slots:
        slot.filled = False
        slot.save()
    
    # If there's a claim, update its status
    if appointment.claim:
        appointment.claim.status = 'initiated'
        appointment.claim.save(update_fields=['status'])
    
    # Delete the appointment
    appointment.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Appointment cancelled successfully'
    })

@login_required
@user_passes_test(is_admin_user)
def delete_timeslot(request, timeslot_id):
    """Delete a time slot if it's not assigned to any appointment"""
    if request.method == 'DELETE':
        timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
        
        # Check if the time slot is already booked
        if timeslot.filled:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete a booked time slot'
            }, status=400)
        
        # Delete the time slot
        timeslot.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Time slot deleted successfully'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
@user_passes_test(is_admin_user)
def approve_quote(request, quote_id):
    """Approve a quote and update its status"""
    if request.method == 'POST':
        try:
            quote = get_object_or_404(Quote, id=quote_id)
            
            # Update quote prices from the form data
            data = json.loads(request.body)
            quote.installation_labor = float(data.get('installation_labor', quote.installation_labor))
            quote.recalabration_costs = float(data.get('recalabration_costs', quote.recalabration_costs))
            
            # Calculate totals
            quote.total_parts_costs = sum(part.cost for part in quote.parts.all())
            quote.total_labor_costs = quote.installation_labor + quote.recalabration_costs
            quote.gross_total = quote.total_parts_costs + quote.total_labor_costs
            
            # Apply tax (assuming a simple rate for now)
            tax_rate = 0.0825  # 8.25% tax
            quote.tax_total = quote.gross_total * tax_rate
            quote.final_total = quote.gross_total + quote.tax_total
            
            quote.save()
            
            # If the quote has a claim, update its status
            if hasattr(quote, 'insurance_claims') and quote.insurance_claims.exists():
                claim = quote.insurance_claims.first()
                claim.status = 'approved'
                claim.save(update_fields=['status'])
            
            return JsonResponse({
                'success': True,
                'message': 'Quote approved successfully',
                'quote_id': quote.id,
                'final_total': quote.final_total
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error approving quote: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)