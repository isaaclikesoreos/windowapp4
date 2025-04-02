import logging
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string

# For SMS, we'll use Twilio (one of the most popular SMS services)
# You'll need to install the twilio package: pip install twilio
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

logger = logging.getLogger(__name__)

def send_quote_email(quote):
    """Send an email with quote details and pin to the customer"""
    if not quote.job_entry.email:
        logger.warning(f"Cannot send email for quote {quote.id} - no email address provided")
        return False
    
    try:
        # Build the quote URL with the pin
        quote_url = settings.SITE_URL + reverse('quote_lookup', args=[quote.pin])
        
        # Get appropriate context based on quote type
        context = {
            'customer_name': f"{quote.job_entry.first_name} {quote.job_entry.last_name}",
            'quote_pin': quote.pin,
            'quote_url': quote_url,
            'quote_type': quote.get_quote_type_display(),
            'job_entry': quote.job_entry,
            'is_repair': quote.quote_type == 'repair',
            'is_replacement': quote.quote_type == 'replacement',
            'is_insurance': quote.job_entry.has_insurance_claim,
        }
        
        # Render email templates
        html_message = render_to_string('windshields/emails/quote_notification.html', context)
        plain_message = render_to_string('windshields/emails/quote_notification.txt', context)
        
        # Send the email
        send_mail(
            subject=f"Your Glass Quote #{quote.pin} is Ready",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote.job_entry.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully for quote {quote.id} to {quote.job_entry.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email for quote {quote.id}: {str(e)}")
        return False

def send_quote_sms(quote):
    """Send an SMS with quote details and pin to the customer"""
    if not quote.job_entry.phone or not TWILIO_AVAILABLE:
        if not quote.job_entry.phone:
            logger.warning(f"Cannot send SMS for quote {quote.id} - no phone number provided")
        elif not TWILIO_AVAILABLE:
            logger.warning(f"Cannot send SMS for quote {quote.id} - Twilio not available")
        return False
    
    try:
        # Check if Twilio settings are configured
        if not all([
            settings.TWILIO_ACCOUNT_SID, 
            settings.TWILIO_AUTH_TOKEN, 
            settings.TWILIO_PHONE_NUMBER
        ]):
            logger.warning("Twilio settings not configured")
            return False
        
        # Build the quote URL with the pin
        quote_url = settings.SITE_URL + reverse('quote_lookup', args=[quote.pin])
        
        # Format phone number (remove any non-digit characters)
        phone = ''.join(filter(str.isdigit, quote.job_entry.phone))
        if not phone.startswith('1'):
            phone = '1' + phone  # Add US country code if not present
        
        # Prepare message
        message = (
            f"Your glass quote #{quote.pin} is ready. "
            f"View details at {quote_url} or enter pin {quote.pin} on our website."
        )
        
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Send message
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+{phone}"
        )
        
        logger.info(f"SMS sent successfully for quote {quote.id} to {quote.job_entry.phone}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send SMS for quote {quote.id}: {str(e)}")
        return False

def send_quote_notifications(quote):
    """Send both email and SMS notifications for a quote"""
    email_sent = send_quote_email(quote)
    sms_sent = send_quote_sms(quote)
    
    # Mark the pin as sent if either method was successful
    if email_sent or sms_sent:
        quote.pin_sent = True
        quote.save(update_fields=['pin_sent'])
        
    return {
        'email_sent': email_sent,
        'sms_sent': sms_sent
    }