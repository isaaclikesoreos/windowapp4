
import random
import string
from django.db import models
from django.conf import settings
from a_users.models import Customer, Vehicle

def generate_unique_pin():
    """Generate a unique 6-character alphanumeric pin for quotes"""
    while True:
        # Generate a 6-character alphanumeric pin
        pin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Check if this pin already exists
        if not Quote.objects.filter(pin=pin).exists():
            return pin


class JobEntry(models.Model):
    # Step 1 – Damage Information
    DAMAGE_PIECE_CHOICES = [
        ('windshield', 'Windshield'),
        ('front_door_glass', 'Front Door Glass'),
        ('rear_door_glass', 'Rear Door Glass'),
        ('back_glass', 'Back Glass'),
        ('quarter_glass', 'Quarter Glass'),
        ('vent_glass', 'Vent Glass'),
    ]
    SIDE_CHOICES = [
        ('driver', 'Driver'),
        ('passenger', 'Passenger'),
    ]
    CAUSE_OF_DAMAGE_CHOICES = [
        ('foreign_object', 'Foreign Object'),
        ('vandalism', 'Vandalism'),
        ('unknown', 'Unknown'),
        ('other', 'Other'),
    ]
    
    damage_piece = models.CharField(
        max_length=20,
        choices=DAMAGE_PIECE_CHOICES,
        help_text="Select the piece of glass that was damaged."
    )
    # For door glass, store passenger/driver selection in damage_side.
    damage_side = models.CharField(
        max_length=10,
        choices=SIDE_CHOICES,
        blank=True,
        null=True,
        help_text="Select door side (Driver or Passenger) if applicable."
    )
    cause_of_damage = models.CharField(
        max_length=20,
        choices=CAUSE_OF_DAMAGE_CHOICES,
        help_text="Select the cause of damage."
    )
    impacting_driving = models.BooleanField(
        help_text="Is this impacting your ability to drive?"
    )
    
    # For windshields, store if the glass is repairable.
    is_repairable = models.BooleanField(
        null=True,
        blank=True,
        help_text="Is the windshield repairable?"
    )
    
    is_quarter_damage = models.BooleanField(
        null=True,
        blank=True,
        help_text="Is the damage quarter sized or smaller? (Only applicable for windshields)"
    )
    
    # Step 3 – Customer Information
    first_name = models.CharField(max_length=50, help_text="Your first name")
    last_name = models.CharField(max_length=50, help_text="Your last name")
    phone = models.CharField(max_length=20, help_text="Your phone number")
    email = models.EmailField(blank=True, null=True, help_text="Your email (optional)")
    vin = models.CharField(
        max_length=17,
        help_text="Vehicle Identification Number (VIN)"
    )
    
    has_insurance_claim = models.BooleanField(
        default=False,
        help_text="Do you already have an insurance claim?"
    )
    insurance_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Insurance company name (if applicable)"
    )
    policy_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Insurance policy number (if applicable)"
    )
    # New field for claim number:
    claim_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Claim number (if applicable)"
    )
    referral_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Referral number (optional)"
    )
    
    has_extended_warranty = models.BooleanField(
        default=False,
        help_text="Have you purchased an extended warranty contract?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"JobEntry for {self.first_name} {self.last_name} - {self.damage_piece}"

class Quote(models.Model):
    # New field to indicate if this quote is for a repair or replacement.
    QUOTE_TYPE_CHOICES = [
        ('repair', 'Repair'),
        ('replacement', 'Replacement'),
    ]
    quote_type = models.CharField(max_length=20, choices=QUOTE_TYPE_CHOICES, null=True, blank=True)
    
    job_entry = models.ForeignKey(
        JobEntry,
        on_delete=models.CASCADE,
        related_name='quotes',
        null=True,    # Allow nulls temporarily
        blank=True
    )

    # If an insurance claim exists, link it (optional)
    claim = models.ForeignKey('InsuranceClaim', on_delete=models.CASCADE, related_name='quotes', null=True, blank=True)
    
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # assuming the customer is the logged-in user
        related_name='quotes',
        on_delete=models.CASCADE
    )
    vehicle = models.ForeignKey(
        Vehicle,
        related_name='quotes',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)
    
    installation_labor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recalabration_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recalabration_type = models.CharField(max_length=50, blank=True, null=True)
    recalabration_description = models.TextField(blank=True, null=True)
    
    total_parts_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_labor_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Changed pin field to have a random default instead of a callable
    pin = models.CharField(max_length=6, unique=True, default='')
    
    # New field to track if pin has been sent to customer
    pin_sent = models.BooleanField(default=False)
    
    parts = models.ManyToManyField('Part', through='QuotePart', related_name='quotes')
    
    def __str__(self):
        return f"Quote {self.pin} for JobEntry {self.job_entry.id if self.job_entry else 'N/A'}"
    
    def save(self, *args, **kwargs):
        if not self.pin:
            # Generate a unique pin here before saving
            while True:
                pin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not Quote.objects.filter(pin=pin).exists():
                    self.pin = pin
                    break
        super().save(*args, **kwargs)

class InsuranceClaim(models.Model):
    customer = models.ForeignKey(
        Customer,
        related_name='insurance_claims',
        on_delete=models.CASCADE
    )
    insurance_name = models.CharField(max_length=100)
    insurance_id = models.CharField(max_length=50)
    referral_number = models.CharField(max_length=50)
    dispatch_number = models.CharField(max_length=50)
    deductible = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='initiated')
    loss_date = models.DateField()
    assigned_date = models.DateField(null=True, blank=True)
    
    DAMAGE_AREA_CHOICES = (
        ('windshield', 'Windshield'),
        ('front_door_glass', 'Front Door Glass'),
        ('rear_door_glass', 'Rear Door Glass'),
        ('back_glass', 'Back Glass'),
        ('quarter_glass', 'Quarter Glass'),
        ('vent_glass', 'Vent Glass'),
    )
    damage_area = models.CharField(max_length=20, choices=DAMAGE_AREA_CHOICES)
    
    SIDE_CHOICES = (
        ('driver', 'Driver'),
        ('passenger', 'Passenger'),
    )
    damage_side = models.CharField(max_length=10, choices=SIDE_CHOICES, null=True, blank=True)
    
    # Link the claim to the quote, if applicable.
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='insurance_claims', null=True, blank=True)
    
    def __str__(self):
        return f"Claim {self.id} for {self.customer}"


# adjust import as needed

class Part(models.Model):
    MAKE_CHOICES = [
        ('OEM', 'OEM'),
        ('aftermarket', 'Aftermarket'),
    ]
    
    part_number = models.CharField(max_length=50, unique=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    make = models.CharField(max_length=20, choices=MAKE_CHOICES)
    
    def __str__(self):
        return f"Part {self.part_number} ({self.make})"


class QuotePart(models.Model):
    quote = models.ForeignKey(
        Quote,
        related_name='quote_parts',
        on_delete=models.CASCADE
    )
    part = models.ForeignKey(
        Part,
        related_name='quote_parts',
        on_delete=models.CASCADE,
        null=True,  # Allow null values for now
        blank=True
    )
    # Additional fields (if needed)
    
    def __str__(self):
        return f"{self.part.part_number if self.part else 'No Part'} for Quote {self.quote.id}"




class TimeSlot(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    filled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Appointment(models.Model):
    claim = models.ForeignKey(
        InsuranceClaim,
        related_name='appointments',
        on_delete=models.CASCADE,
        null=True,  # if appointment is optional or can be created without a claim
        blank=True
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='appointments',
        on_delete=models.CASCADE
    )
    vehicle = models.ForeignKey(
        Vehicle,
        related_name='appointments',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    appointment_date = models.DateTimeField()  # could represent the start of the appointment
    service_location = models.CharField(max_length=100)
    timeslots = models.ManyToManyField(TimeSlot, related_name='appointments', blank=True)
    
    def __str__(self):
        return f"Appointment for Claim {self.claim.id if self.claim else 'N/A'} on {self.appointment_date}"

class ShopSetting(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    labor_rate = models.DecimalField(max_digits=6, decimal_places=2)
    repair_rate = models.DecimalField(max_digits=6, decimal_places=2)
    timezone = models.CharField(max_length=50)
    # We'll store hours as a JSON object mapping weekday names to [start, end] times.
    # Example: {"Monday": ["09:00", "17:00"], "Tuesday": ["09:00", "17:00"], ...}
    hours_of_operation = models.JSONField()
    mobile_service = models.BooleanField(default=False)

    def __str__(self):
        return self.name