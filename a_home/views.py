
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, FormView
from django.http import Http404
from django.urls import reverse
from django import forms

from .models import Quote

@login_required
def home(request):
    context = {
        'user': request.user,  # Pass the logged-in user to the template
    }
    return render(request, 'home.html', context)




class QuotePinForm(forms.Form):
    """Form for looking up quotes by pin"""
    pin = forms.CharField(
        max_length=6, 
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg py-2 px-3 bg-white border text-center uppercase', 
            'placeholder': 'Enter 6-character PIN'
        })
    )

class QuoteLookupFormView(FormView):
    """View for the quote lookup form on the home page"""
    template_name = 'windshields/quote_lookup_form.html'
    form_class = QuotePinForm
    
    def form_valid(self, form):
        pin = form.cleaned_data['pin'].upper()
        return redirect('quote_lookup', pin=pin)

def quote_lookup_view(request, pin):
    """View to look up and display a quote by pin"""
    try:
        quote = Quote.objects.get(pin=pin.upper())
        
        # Determine which view to redirect to based on quote type
        if quote.quote_type == 'repair':
            if quote.job_entry.has_insurance_claim:
                redirect_url = reverse('insurance_repair_quote')
            else:
                redirect_url = reverse('repair_quote')
        else:  # replacement
            if quote.job_entry.has_insurance_claim:
                redirect_url = reverse('insurance_replacement_quote')
            else:
                redirect_url = reverse('replacement_quote')
        
        # Add parameters to prevent sending notifications again
        redirect_url += f'?job_entry_id={quote.job_entry.id}&no_notify=1'
        
        return redirect(redirect_url)
    
    except Quote.DoesNotExist:
        # Handle invalid pin
        context = {
            'error': 'Invalid quote PIN. Please check and try again.',
            'form': QuotePinForm(initial={'pin': pin})
        }
        return render(request, 'windshields/quote_lookup_form.html', context)
    


def resend_quote_notification(request, quote_id):
    """View to resend a quote notification (email and SMS)"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=403)
    
    try:
        quote = Quote.objects.get(id=quote_id, customer=request.user)
        
        # Mark pin as not sent to force resending
        quote.pin_sent = False
        quote.save(update_fields=['pin_sent'])
        
        # Send the notifications
        from .utils import send_quote_notifications
        notification_result = send_quote_notifications(quote)
        
        return JsonResponse({
            'success': True,
            'message': 'Quote notification resent successfully',
            'details': notification_result
        })
    
    except Quote.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Quote not found or you do not have permission to access it'
        }, status=404)